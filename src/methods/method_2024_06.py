import json
from typing import List, Dict
from bs4 import BeautifulSoup


def scrape_posts_from_html(html: str) -> List[Dict]:
    """
    Scrape posts from Threads HTML source code (June 2024 version).
    Returns a list of dicts with keys: content, datetime, user, image, likes, comments.
    """
    soup = BeautifulSoup(html, "html.parser")

    script = soup.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return []

    try:
        data = json.loads(script.string)
    except json.JSONDecodeError:
        return []

    posts = []
    for entry in data.get("posts", []):
        posts.append(
            {
                "id": entry.get("id"),
                "user": entry.get("user"),
                "datetime": entry.get("datetime"),
                "content": entry.get("content"),
                "image": entry.get("image"),
                "likes": entry.get("likes"),
                "comments": entry.get("comments"),
            }
        )

    return posts
