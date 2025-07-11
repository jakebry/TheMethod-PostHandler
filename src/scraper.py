import requests
from src.config import USER_URL, USER_AGENT, NEW_SOURCE_CODE_PATH, ROTATION_HISTORY_PATH
from src.utils import load_json, save_json
from src.methods.method_2024_06 import scrape_posts_from_html
from datetime import datetime


def download_html(url: str) -> str:
    headers = {"User-Agent": USER_AGENT}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def update_rotation_history(method_name: str, status: str) -> None:
    history = load_json(ROTATION_HISTORY_PATH)
    now = datetime.utcnow().isoformat()
    history.append({"method": method_name, "status": status, "timestamp": now})
    save_json(ROTATION_HISTORY_PATH, history)

def scrape_threads() -> list:
    html = download_html(USER_URL)
    posts = scrape_posts_from_html(html)
    if not posts:
        # Save HTML for inspection
        with open(NEW_SOURCE_CODE_PATH, 'w', encoding='utf-8') as f:
            f.write(html)
        update_rotation_history("method_2024_06", "failed")
        raise RuntimeError("Scraping failed. Source code saved for inspection.")
    update_rotation_history("method_2024_06", "success")
    return posts
