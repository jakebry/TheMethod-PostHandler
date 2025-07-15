from pathlib import Path
from src.methods.method_1 import extract_posts

NESTED_HTML = Path("tests/data/nested_post.html").read_text()

def test_extract_posts_nested():
    posts = extract_posts(NESTED_HTML)
    assert len(posts) == 2
    assert posts[0]["content"].startswith("🟢Buy")
    assert posts[0]["datetime"] == "2025-06-16T08:55:01.000Z"
    assert posts[1]["content"].startswith("SL: 0.789")
    assert posts[1]["datetime"] == "2025-06-16T08:56:30.000Z"

