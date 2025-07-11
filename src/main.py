from src.scraper import scrape_threads
from src.utils import load_json, save_json, deduplicate_posts, sort_posts_newest_first
from src.config import POSTS_JSON_PATH


def main():
    try:
        new_posts = scrape_threads()
    except Exception as e:
        print(f"Error: {e}")
        return

    existing_posts = load_json(POSTS_JSON_PATH)
    all_posts = new_posts + existing_posts
    all_posts = deduplicate_posts(all_posts)
    all_posts = sort_posts_newest_first(all_posts)
    save_json(POSTS_JSON_PATH, all_posts)
    print(f"Scraped {len(new_posts)} new posts. Total posts: {len(all_posts)}.")

if __name__ == "__main__":
    main()
