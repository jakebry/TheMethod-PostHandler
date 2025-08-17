import os

# Configuration constants for Threads Scraper

# Optional: default handle for local/manual testing only. Prefer using trusted sources from DB.
THREADS_USER = os.getenv("THREADS_USER", "example_user")
USER_URL = f"https://www.threads.net/@{THREADS_USER}"
POSTS_JSON_PATH = "data/posts.json"
NEW_SOURCE_CODE_PATH = "new_source_code.html"
