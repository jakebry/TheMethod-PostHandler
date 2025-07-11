from pathlib import Path
from src.methods.method_2024_06 import scrape_posts_from_html

def test_scrape_posts_from_html():
    html = Path("tests/data/sample_source_2024_06.html").read_text()
    posts = scrape_posts_from_html(html)
    assert len(posts) == 2
    assert posts[0]["content"] == "First post"
    assert posts[1]["likes"] == 150
