from src.scraper import scrape_and_store_posts
from src.method_tracker import log_method_working, log_method_stopped
from src.console_anim import Spinner
from src.service_role_setup import initialize_service_role
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    # Initialize service role key for database trigger authentication
    print("Initializing service role key for database trigger...")
    if not initialize_service_role():
        print("❌ Failed to initialize service role key. Exiting.")
        return
    
    spinner = Spinner("Scraping threads and storing in Supabase")
    spinner.start()
    try:
        # Attempt to scrape posts
        method_working = scrape_and_store_posts()
        
        if method_working:
            # Method is working - update the working status
            log_method_working()
            print("Method is working - successfully extracted posts.")
        else:
            # Method failed - mark it as stopped
            log_method_stopped()
            print("Method stopped - no posts could be extracted.")
            
    except Exception as e:
        print(f"Error: {e}")
        # Method failed due to exception - mark it as stopped
        log_method_stopped()
        return
    finally:
        spinner.stop()

    print("Scraping process completed.")

if __name__ == "__main__":
    try:
        main()
        print("[END] Scraper finished")
    except KeyboardInterrupt:
        print("[INFO] Received SIGINT (KeyboardInterrupt), shutting down gracefully.")
