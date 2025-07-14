from src.methods.method_1 import scrape_threads
from src.utils import load_json, save_json, deduplicate_posts, sort_posts_newest_first
from src.config import POSTS_JSON_PATH
from src.method_tracker import log_method_start, log_method_stop


def main():
    try:
        new_posts = scrape_threads()
        if new_posts and len(new_posts) > 0:
            log_method_start()
        else:
            print("[ERROR] No posts parsed. Marking method as stopped.")
            log_method_stop()
    except Exception as e:
        print(f"Error: {e}")
        log_method_stop()
        return

    existing_posts = load_json(POSTS_JSON_PATH)
    all_posts = new_posts + existing_posts
    all_posts = deduplicate_posts(all_posts)
    all_posts = sort_posts_newest_first(all_posts)
    save_json(POSTS_JSON_PATH, all_posts)
    print(f"Scraped {len(new_posts)} new posts. Total posts: {len(all_posts)}.")

if __name__ == "__main__":
    main()
