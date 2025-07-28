from src.config import USER_URL, NEW_SOURCE_CODE_PATH
from src.browser_manager import get_browser_manager, cleanup_browser_manager
from bs4 import BeautifulSoup
import re
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

def download_html_playwright(url: str, profile_name: str = "threads_scraper", session_name: str = None) -> str:
    """
    Download HTML using optimized browser manager with session persistence.
    
    Args:
        url: The URL to scrape
        profile_name: Browser profile name for persistence
        session_name: Session name for cookie/storage restoration
    
    Returns:
        HTML content as string
    """
    browser_manager = get_browser_manager()
    
    try:
        # Create page with optimized settings
        page = browser_manager.create_page(profile_name, session_name)
        
        # Add random delays to avoid detection
        import random
        import time
        
        # Navigate to the page
        logger.info(f"Navigating to: {url}")
        page.goto(url, timeout=60000, wait_until="networkidle")
        
        # Random delay to simulate human behavior
        time.sleep(random.uniform(2, 5))
        
        # Scroll a bit to simulate human interaction
        page.evaluate("window.scrollTo(0, Math.random() * 500)")
        time.sleep(random.uniform(1, 3))
        
        # Wait for content to load
        page.wait_for_load_state('networkidle')
        
        # Get the HTML content
        html = page.content()
        
        # Save session for future use
        if session_name:
            browser_manager.save_current_session(session_name)
        
        logger.info(f"Successfully downloaded HTML from {url}")
        return html
        
    except Exception as e:
        logger.error(f"Error downloading HTML from {url}: {e}")
        raise
    finally:
        # Don't close the browser manager here - let it be reused
        pass

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
    soup = BeautifulSoup(html, "html.parser")
    profile_username = extract_profile_username(soup)
    logger.debug("Profile username: %s", profile_username)

    # Check for JSON data first (used in unit tests)
    script = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if script and script.string:
        try:
            data = json.loads(script.string)
            posts = [
                {
                    "id": p.get("id"),
                    "user": p.get("user") or profile_username,
                    "datetime": p.get("datetime"),
                    "content": p.get("content"),
                    "image": p.get("image"),
                }
                for p in data.get("posts", [])
            ]
            logger.debug("Extracted %d posts from JSON data.", len(posts))
            return posts
        except Exception:
            pass

    posts = []
    # Stricter regex: /@username/post/<id> (no trailing /media)
    post_link_re = re.compile(r"/@[\w.]+/post/[A-Za-z0-9_-]+$")
    post_links = soup.find_all("a", href=post_link_re)
    logger.debug("Found %d post permalinks.", len(post_links))
    date_re = re.compile(r"\d{2}/\d{2}/\d{2}")
    for link in post_links:
        post = {}
        # ID from permalink
        m = re.search(r"/post/([A-Za-z0-9_-]+)$", link.get("href", ""))
        if m:
            post["id"] = m.group(1)
        # Datetime: <time> tag inside the link
        time_tag = link.find("time", datetime=True)
        post["datetime"] = time_tag["datetime"] if time_tag else None
        # Walk up the tree until we reach the post container
        ancestor = link
        for _ in range(10):
            if ancestor.has_attr("data-pressable-container"):
                break
            if ancestor.parent:
                ancestor = ancestor.parent
            else:
                break
        logger.debug("Ancestor tag for permalink: <%s>", ancestor.name)
        # Username: first <a href="/@username"> in ancestor's subtree
        username = None
        user_a = ancestor.find("a", href=re.compile(r"/@[\w.]+$"))
        if user_a:
            username_span = user_a.find("span")
            if username_span:
                username = username_span.get_text(strip=True)
            else:
                username = user_a.get_text(strip=True)
        if not username:
            user_span = ancestor.find("span", string=re.compile(r"^[A-Za-z0-9_.]+$"))
            if user_span:
                username = user_span.get_text(strip=True)
        # Fallback to profile username if not found
        if not username:
            username = profile_username
        logger.debug("Username found: %s", username)
        post["user"] = username
        # Content: for each <span> in ancestor, not inside <a> or <time>, use span.get_text(strip=True)
        content = None
        max_len = 0
        def valid_text(text):
            if not text:
                return False
            if text == username:
                return False
            if date_re.fullmatch(text):
                return False
            return True
        for span in ancestor.find_all("span"):
            # Skip if inside <a> or <time>
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
            if valid_text(text) and len(text) > max_len:
                content = text
                max_len = len(text)
        logger.debug("Content found: %s", content)
        post["content"] = content
        # Image: use extract_post_image helper
        image_url = extract_post_image(ancestor)
        post["image"] = image_url
        # Only keep posts with both username and content
        if post["user"] and post["content"]:
            posts.append(post)
        else:
            logger.debug("Skipped post: user=%s content=%s", post['user'], post['content'])
    logger.debug("Extracted %d posts.", len(posts))
    return posts

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
