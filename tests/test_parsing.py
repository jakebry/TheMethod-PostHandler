import os
import sys
import json
from bs4 import BeautifulSoup
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from threads_scraper import extract_posts, find_thread_items, clean_text

SAMPLE_JSON = {
    "props": {
        "pageProps": {
            "feed": {
                "threads": [
                    {
                        "thread_items": [
                            {
                                "post": {
                                    "caption": {"text": "Hello world"},
                                    "taken_at": 1710000000,
                                    "image_versions2": {
                                        "candidates": [
                                            {"url": "https://example.com/img1.jpg?size=small"},
                                            {"url": "https://example.com/img1.jpg?size=large"},
                                            {"url": "https://example.com/avatar.jpg"}
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    }
}


def test_extract_posts_deduplicates_and_skips_avatar():
    html = f'<html><body><script type="application/json">{json.dumps(SAMPLE_JSON)}</script></body></html>'
    soup = BeautifulSoup(html, "html.parser")
    posts = extract_posts(soup, avatar_url="https://example.com/avatar.jpg")
    assert len(posts) == 1
    post = posts[0]
    assert post["content"] == "Hello world"
    assert post["timestamp"] == datetime.utcfromtimestamp(1710000000).isoformat() + "Z"
    assert post["images"] == ["https://example.com/img1.jpg?size=small"]


def test_find_thread_items_recurses():
    obj = {
        "a": {"thread_items": [1, 2]},
        "b": [
            {"thread_items": [3]},
            {"c": {"thread_items": [4]}}
        ]
    }
    assert find_thread_items(obj) == [1, 2, 3, 4]


def test_clean_text_removes_interaction_words():
    text = "Hello world\nLike 10 Comment 2 Repost 1 Share 3"
    assert clean_text(text) == "Hello world"
