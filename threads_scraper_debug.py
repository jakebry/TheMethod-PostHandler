import time
import re
import json
import logging
from collections import Counter
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# CONFIG
TARGET_USER = "j.p_morgan_trading"
THREADS_URL = f"https://www.threads.net/@{TARGET_USER}"
TXT_OUTPUT = f"{TARGET_USER}_threads.txt"
JSON_OUTPUT = f"{TARGET_USER}_threads.json"
SCROLL_PAUSE_SEC = 2

# LOGGING
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--lang=en-US")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    return webdriver.Chrome(options=options)

def scroll_to_bottom(driver, pause=SCROLL_PAUSE_SEC):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def detect_profile_avatar(soup):
    images = [img["src"] for img in soup.find_all("img") if "src" in img.attrs]
    if not images:
        return None
    return Counter(images).most_common(1)[0][0]

def clean_text(text):
    text = re.sub(r"(Like|Comment|Repost|Share)[^\n]*", "", text)
    return text.strip()

def extract_posts(soup, avatar_url=None):
    logging.info("Looking for embedded JSON with post data...")
    posts = []

    scripts = soup.find_all("script", {"type": "application/json"})

    for script in scripts:
        try:
            data = json.loads(script.string)

            # Attempt to dig into nested JSON structure
            thread_items = (
                data.get("props", {})
                    .get("pageProps", {})
                    .get("thread_items", [])
            )

            for item in thread_items:
                post_data = item.get("post", {})
                content = post_data.get("text", "").strip()
                timestamp = post_data.get("creation_time", "unknown")

                images = []
                media = post_data.get("media", [])
                for m in media:
                    if m.get("type") == "image" and m.get("url"):
                        images.append(m["url"])

                if content:
                    posts.append({
                        "content": content,
                        "timestamp": timestamp,
                        "images": images or None
                    })

        except Exception as e:
            logging.warning(f"Skipping script due to error: {e}")

    logging.info(f"✅ Extracted {len(posts)} posts from embedded JSON.")
    return posts

def save_as_text(posts, path):
    with open(path, "w", encoding="utf-8") as f:
        for post in posts:
            f.write(f"Content: {post['content']}\n")
            f.write("Images:\n")
            if post["images"]:
                f.write("\n".join(post["images"]) + "\n")
            else:
                f.write("(none)\n")
            f.write(f"Timestamp: {post['timestamp']}\n")
            f.write("-" * 40 + "\n")

def save_as_json(posts, path):
    """Save posts to a single pretty-printed JSON array."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def dump_script_tags(soup):
    scripts = soup.find_all("script", {"type": "application/json"})
    logging.info(f"Found {len(scripts)} <script type='application/json'> blocks")

    for i, script in enumerate(scripts):
        try:
            script_content = script.string or script.text
            if not script_content:
                logging.warning(f"Script {i} is empty, skipping.")
                continue

            with open(f"script_{i}.json", "w", encoding="utf-8") as f:
                f.write(script_content)
            logging.info(f"📝 Saved script_{i}.json")
        except Exception as e:
            logging.warning(f"⚠️ Could not save script_{i}.json: {e}")

def main():
    driver = init_driver()
    try:
        logging.info(f"Opening {THREADS_URL}")
        driver.get(THREADS_URL)
        time.sleep(5)

        logging.info("Scrolling through page...")
        scroll_to_bottom(driver)

        # 🛠 Save raw page HTML
        with open("debug_threads_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("🔍 Saved debug_threads_page.html for inspection")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Dump all JSON script blocks to separate files
        dump_script_tags(soup)

        # Optional: Avatar detection (in case you want to skip post avatars)
        avatar_url = detect_profile_avatar(soup)
        if avatar_url:
            logging.info(f"Detected profile avatar: {avatar_url}")

        # Try extracting posts from embedded JSON
        posts = extract_posts(soup, avatar_url)
        save_as_text(posts, TXT_OUTPUT)
        save_as_json(posts, JSON_OUTPUT)

        logging.info(f"✅ Saved posts to: {TXT_OUTPUT} and {JSON_OUTPUT}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
