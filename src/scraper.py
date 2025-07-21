import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from src.methods.method_1 import download_html_playwright, extract_posts

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
    """
    supabase = init_supabase_client()
    
    # Authenticate as a service user
    email = os.getenv("SUPABASE_USER_EMAIL")
    password = os.getenv("SUPABASE_USER_PASSWORD")

    if not email or not password:
        logger.error("Scraper user email and password must be set in the .env file.")
        return

    try:
        logger.info(f"Authenticating as {email}...")
        supabase.auth.sign_in_with_password({"email": email, "password": password})
        logger.info("Authentication successful.")
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        return

    trusted_sources = get_trusted_sources(supabase)
    
    if not trusted_sources:
        logger.info("No trusted sources found to scrape.")
        return

    for account_handle in trusted_sources:
        logger.info(f"Scraping posts for: {account_handle}")
        try:
            user_url = f"https://www.threads.net/@{account_handle}"
            html = download_html_playwright(user_url)
            posts = extract_posts(html)

            if not posts:
                logger.info(f"No new posts found for {account_handle}.")
                continue

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
                    # Upsert based on a unique constraint (e.g., account_handle and content)
                    # This example assumes a unique combination of account_handle and datetime,
                    # you might need to adjust based on your actual table constraints.
                    # As a simple approach, we check if a similar post exists.
                    # A more robust solution might use a unique post ID from Threads if available.
                    
                    # Check for existing post to avoid duplicates
                    existing_post_response = supabase.table("user_posts").select("id").eq("account_handle", account_handle).eq("content", post.get("content")).execute()

                    if not existing_post_response.data:
                        supabase.table("user_posts").insert(post_data).execute()
                        logger.info(f"Inserted new post for {account_handle}.")
                    else:
                        logger.info(f"Post already exists for {account_handle}, skipping.")
                except Exception as e:
                    logger.error(f"Error saving post to Supabase for {account_handle}: {e}")

        except Exception as e:
            logger.error(f"Failed to scrape or store posts for {account_handle}: {e}")

if __name__ == "__main__":
    scrape_and_store_posts() 