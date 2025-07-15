from src.config import USER_URL, NEW_SOURCE_CODE_PATH
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from src.utils import deduplicate_posts
import json
import re

def download_html_playwright(url: str) -> str:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_load_state('networkidle')
        html = page.content()
        browser.close()
        return html

def extract_profile_username(soup):
    import re
    # Try to find <a> with href="/@username" near the top of the page
    for a in soup.find_all("a", href=True):
        if re.match(r"^/@[A-Za-z0-9_.]+$", a["href"]):
            span = a.find("span")
            if span:
                return span.get_text(strip=True)
            return a.get_text(strip=True)
    return None

def extract_posts(html: str):
    """Extract posts from Threads HTML. The function first tries to parse the
    `__NEXT_DATA__` JSON payload which contains clean post information. If that
    fails it falls back to a best effort DOM scrape which tries to skip nested
    replies."""

    soup = BeautifulSoup(html, "html.parser")

    # Try JSON payload first
    json_script = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if json_script and json_script.string:
        try:
            data = json.loads(json_script.string)
            json_posts = data.get("posts") or data.get("props", {}).get("pageProps", {}).get("posts")
            if isinstance(json_posts, list) and json_posts:
                posts = []
                for post in json_posts:
                    # Skip replies if the JSON has a reference to a parent
                    if any(key in post for key in ("parent_post_id", "replied_to_post_id", "thread_id")):
                        if post.get("parent_post_id") or post.get("replied_to_post_id"):
                            continue
                    posts.append({
                        "id": post.get("id"),
                        "user": post.get("user"),
                        "content": post.get("content"),
                        "datetime": post.get("datetime"),
                        "image": post.get("image"),
                    })
                return deduplicate_posts(posts)
        except Exception as e:  # pragma: no cover - debug information only
            print(f"[DEBUG] Failed to parse __NEXT_DATA__: {e}")

    profile_username = extract_profile_username(soup)
    print(f"[DEBUG] Profile username: {profile_username}")

    posts = []
    post_link_re = re.compile(r"/@[\w.]+/post/[A-Za-z0-9_-]+$")
    post_links = soup.find_all("a", href=post_link_re)
    print(f"[DEBUG] Found {len(post_links)} post permalinks.")
    seen_links = set()
    date_re = re.compile(r"\d{2}/\d{2}/\d{2}")

    for link in post_links:
        href = link.get("href")
        if href in seen_links:
            continue
        seen_links.add(href)

        post = {}
        time_tag = link.find("time", datetime=True)
        post["datetime"] = time_tag["datetime"] if time_tag else None

        ancestor = link
        for _ in range(10):
            if ancestor.parent:
                ancestor = ancestor.parent
            else:
                break
        print(f"[DEBUG] Ancestor tag for permalink: <{ancestor.name}>")

        username = None
        for user_a in ancestor.find_all("a", href=re.compile(r"/@[\w.]+$")):
            username_span = user_a.find("span")
            text = username_span.get_text(strip=True) if username_span else user_a.get_text(strip=True)
            if text:
                username = text
                break
        if not username:
            username = profile_username
        print(f"[DEBUG] Username found: {username}")
        post["user"] = username

        content = None
        for span in ancestor.find_all("span"):
            parent = span.parent
            skip = False
            while parent and parent != ancestor:
                if parent.name in ("a", "time"):
                    skip = True
                    break
                parent = parent.parent
            if skip:
                continue
            text = span.get_text(strip=True)
            if text and text != username and not date_re.fullmatch(text):
                content = text
                break
        print(f"[DEBUG] Content found: {content}")
        post["content"] = content

        image_url = extract_post_image(ancestor)
        post["image"] = image_url

        if post["user"] and post["content"]:
            posts.append(post)
        else:
            print(f"[DEBUG] Skipped post: user={post['user']} content={post['content']}")

    print(f"[DEBUG] Extracted {len(posts)} posts.")
    return deduplicate_posts(posts)

def scrape_threads():
    html = download_html_playwright(USER_URL)
    return extract_posts(html)

def extract_post_image(ancestor):
    import re
    # Prefer <img> inside <a> with /media in href
    for a in ancestor.find_all("a", href=True):
        if "/media" in a["href"]:
            img = a.find("img", src=True)
            if img:
                return img["src"]
    # Otherwise, find all <img> tags not inside <a> with /@username in href
    for img in ancestor.find_all("img", src=True):
        parent_a = img.find_parent("a", href=True)
        if parent_a and re.match(r"^/@[A-Za-z0-9_.]+$", parent_a["href"]):
            continue  # skip profile image
        return img["src"]
    return None 