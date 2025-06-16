import time
import re
import json
import logging
from datetime import datetime
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
    logging.info("📦 Parsing from props → pageProps → feed → threads")
    posts = []

    scripts = soup.find_all("script", {"type": "application/json"})
    for script in scripts:
        try:
            data = json.loads(script.string or script.text)

            threads = (
                data.get("props", {})
                    .get("pageProps", {})
                    .get("feed", {})
                    .get("threads", [])
            )

            for thread in threads:
                for item in thread.get("thread_items", []):
                    post = item.get("post", {})
                    caption = post.get("caption", {}).get("text", "")
                    if not caption.strip():
                        continue

                    # Convert UNIX timestamp to ISO format
                    timestamp_unix = post.get("taken_at")
                    if timestamp_unix:
                        timestamp = datetime.utcfromtimestamp(timestamp_unix).isoformat() + "Z"
                    else:
                        timestamp = "unknown"

                    images = [
                        img["url"]
                        for img in post.get("image_versions2", {}).get("candidates", [])
                        if "url" in img
                    ]

                    posts.append({
                        "content": caption.strip(),
                        "timestamp": timestamp,
                        "images": images or None
                    })

        except Exception as e:
            logging.warning(f"⚠️ Failed to parse a script block: {e}")
            continue

    logging.info(f"✅ Extracted {len(posts)} posts from final confirmed schema.")
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
    with open(path, "w", encoding="utf-8") as f:
        for post in posts:
            json.dump(post, f)
            f.write("\n")

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

        # Save raw page HTML
        with open("debug_threads_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("🔍 Saved debug_threads_page.html for inspection")

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Dump script blocks for inspection
        dump_script_tags(soup)

        avatar_url = detect_profile_avatar(soup)
        if avatar_url:
            logging.info(f"Detected profile avatar: {avatar_url}")

        posts = extract_posts(soup, avatar_url)
        save_as_text(posts, TXT_OUTPUT)
        save_as_json(posts, JSON_OUTPUT)

        logging.info(f"✅ Saved posts to: {TXT_OUTPUT} and {JSON_OUTPUT}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
