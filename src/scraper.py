import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from src.methods.method_1 import download_html_playwright, extract_posts
from src.browser_manager import cleanup_browser_manager
import time

# Load environment variables from .env file
# Construct the path to the .env file relative to this script's location
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def init_supabase_client() -> Client:
    """Initializes and returns a Supabase client."""
    supabase_url = os.getenv("VITE_SUPABASE_URL")
    # We use the anon key to initialize the client, then authenticate
    supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase URL and Anon Key must be set in the .env file.")
    
    # Remove any trailing % or whitespace from the URL
    supabase_url = supabase_url.strip().rstrip('%')
    
    return create_client(supabase_url, supabase_key)

def get_trusted_sources(supabase: Client):
    """Fetches trusted sources from the Supabase 'trusted_sources' table."""
    try:
        response = supabase.table("trusted_sources").select("account_handle").eq("platform", "Threads").execute()
        if response.data:
            logger.info(f"Found {len(response.data)} trusted sources.")
            return [source["account_handle"] for source in response.data]
        
        logger.warning("No trusted sources with platform='Threads' found in the database.")
        return []
    except Exception as e:
        logger.error(f"Error fetching trusted sources: {str(e)}")
        return []

def scrape_and_store_posts():
    """
    Scrapes posts from Threads for trusted sources and stores them in Supabase.
    Returns True if the method is working (successfully extracted posts), False otherwise.
    """
    supabase = init_supabase_client()
    
    # Authenticate as admin service user
    email = os.getenv("SUPABASE_USER_EMAIL")
    password = os.getenv("SUPABASE_USER_PASSWORD")

    if not email or not password:
        logger.error("Admin user email and password must be set in the .env file.")
        return False

    try:
        logger.info(f"Authenticating as admin user {email}...")
        supabase.auth.sign_in_with_password({"email": email, "password": password})
        logger.info("Authentication successful.")
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return False

    trusted_sources = get_trusted_sources(supabase)
    
    if not trusted_sources:
        logger.info("No trusted sources found to scrape.")
        return False

    total_posts_extracted = 0
    
    try:
        for account_handle in trusted_sources:
            logger.info(f"Scraping posts for: {account_handle}")
            try:
                user_url = f"https://www.threads.net/@{account_handle}"
                
                # Use session management for each account
                session_name = f"threads_session_{account_handle}"
                html = download_html_playwright(user_url, profile_name="threads_scraper", session_name=session_name)
                posts = extract_posts(html)

                if not posts:
                    logger.info(f"No posts extracted for {account_handle}.")
                    continue

                total_posts_extracted += len(posts)
                logger.info(f"Extracted {len(posts)} posts for {account_handle}.")

                # Start timing the database operations
                db_start_time = time.time()
                
                # Prepare all posts for batch processing
                posts_to_insert = []
                posts_to_check = []
                
                for post in posts:
                    # Prepare post data with image handling
                    image_value = post.get("image")
                    
                    # If image is a URL string, use it; otherwise set to None
                    if image_value and isinstance(image_value, str) and (image_value.startswith('http') or image_value.startswith('/')):
                        # This looks like a valid image URL
                        post_data = {
                            "datetime": post.get("datetime"),
                            "account_handle": account_handle,
                            "platform": "Threads",
                            "content": post.get("content"),
                            "image": image_value,  # Use image URL directly
                        }
                    else:
                        # No image or invalid image data
                        post_data = {
                            "datetime": post.get("datetime"),
                            "account_handle": account_handle,
                            "platform": "Threads",
                            "content": post.get("content"),
                            "image": None,  # Set to None for posts without images
                        }
                    
                    posts_to_insert.append(post_data)
                    posts_to_check.append(post.get("content"))

                # Batch check for existing posts (much faster than individual checks)
                if posts_to_check:
                    try:
                        logger.info(f"🔍 Batch checking {len(posts_to_check)} posts for duplicates...")
                        
                        # Use IN clause to check multiple posts at once
                        existing_posts_response = supabase.table("user_posts").select("content").eq("account_handle", account_handle).in_("content", posts_to_check).execute()
                        
                        # Create a set of existing content for fast lookup
                        existing_contents = {post["content"] for post in existing_posts_response.data}
                        
                        # Filter out posts that already exist
                        new_posts = [post for post in posts_to_insert if post["content"] not in existing_contents]
                        
                        if new_posts:
                            logger.info(f"📝 Found {len(new_posts)} new posts to insert for {account_handle}")
                            
                            # Process posts individually to avoid database timeouts
                            successful_inserts = 0
                            posts_with_images = 0
                            posts_without_images = 0
                            
                            for i, post_data in enumerate(new_posts, 1):
                                try:
                                    logger.info(f"📝 Processing post {i}/{len(new_posts)}...")
                                    
                                    # Insert post with image (should work now with fixed trigger)
                                    supabase.table("user_posts").insert(post_data).execute()
                                    successful_inserts += 1
                                    
                                    if post_data["image"]:
                                        posts_with_images += 1
                                        logger.info(f"✅ Inserted post {i} with image for {account_handle}")
                                    else:
                                        posts_without_images += 1
                                        logger.info(f"✅ Inserted post {i} without image for {account_handle}")
                                        
                                except Exception as e:
                                    logger.error(f"❌ Failed to insert post {i} for {account_handle}: {e}")
                            
                            # Summary
                            if successful_inserts > 0:
                                logger.info(f"🎉 Successfully inserted {successful_inserts}/{len(new_posts)} posts")
                                if posts_with_images > 0:
                                    logger.info(f"✅ Posts with images: {posts_with_images}")
                                if posts_without_images > 0:
                                    logger.info(f"✅ Posts without images: {posts_without_images}")
                                    
                                # Performance metrics
                                db_time = time.time() - db_start_time
                                logger.info(f"⚡ Database operations completed in {db_time:.2f}s for {len(new_posts)} posts")
                            else:
                                logger.warning(f"⚠️ No posts were successfully inserted")
                                
                        else:
                            logger.info(f"✅ All posts for {account_handle} already exist, skipping.")
                            
                    except Exception as e:
                        logger.error(f"Error checking existing posts for {account_handle}: {e}")
                        # Fallback to individual processing if batch check fails
                        logger.info(f"⚠️ Falling back to individual post processing for {account_handle}")
                        
                        for post_data in posts_to_insert:
                            try:
                                # Check for existing post to avoid duplicates
                                existing_post_response = supabase.table("user_posts").select("id").eq("account_handle", account_handle).eq("content", post_data["content"]).execute()

                                if not existing_post_response.data:
                                    # Insert post with image (should work now with fixed trigger)
                                    supabase.table("user_posts").insert(post_data).execute()
                                    if post_data["image"]:
                                        logger.info(f"Inserted new post for {account_handle} with image.")
                                    else:
                                        logger.info(f"Inserted new post for {account_handle} without image.")
                                else:
                                    logger.info(f"Post already exists for {account_handle}, skipping.")
                            except Exception as e:
                                logger.error(f"Error saving post to Supabase for {account_handle}: {e}")

            except Exception as e:
                logger.error(f"Failed to scrape or store posts for {account_handle}: {e}")

    finally:
        # Cleanup browser manager
        cleanup_browser_manager()

    # Method is working if we extracted at least some posts
    return total_posts_extracted > 0

if __name__ == "__main__":
    scrape_and_store_posts() 