import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from src.methods.method_1 import download_html_playwright, extract_posts
from src.browser_manager import cleanup_browser_manager

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

                for post in posts:
                    post_data = {
                        "datetime": post.get("datetime"),
                        "account_handle": account_handle,
                        "platform": "Threads",
                        "content": post.get("content"),
                        "image": post.get("image"),
                    }

                    # Insert or update post in Supabase
                    try:
                        # Check for existing post to avoid duplicates
                        existing_post_response = supabase.table("user_posts").select("id").eq("account_handle", account_handle).eq("content", post.get("content")).execute()

                        if not existing_post_response.data:
                            # Insert with image - admin user should have proper permissions
                            supabase.table("user_posts").insert(post_data).execute()
                            logger.info(f"Inserted new post for {account_handle} with image.")
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