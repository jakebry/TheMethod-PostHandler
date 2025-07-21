from src.scraper import scrape_and_store_posts
from src.method_tracker import log_method_start, log_method_stop
from src.console_anim import Spinner
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main():
    spinner = Spinner("Scraping threads and storing in Supabase")
    spinner.start()
    try:
        log_method_start()
        scrape_and_store_posts()
        log_method_stop()
    except Exception as e:
        print(f"Error: {e}")
        log_method_stop()
        return
    finally:
        spinner.stop()

    print("Scraping process completed.")

if __name__ == "__main__":
    main()
