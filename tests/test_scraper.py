from pathlib import Path
from unittest.mock import patch

from src.methods.method_1 import scrape_threads

SAMPLE_HTML = Path("tests/data/sample_source_2024_06.html").read_text()


@patch("src.methods.method_1.download_html_playwright", return_value=SAMPLE_HTML)
def test_scrape_threads(mock_download):
    posts = scrape_threads()
    assert len(posts) == 2
    # First post
    assert posts[0]["user"] == "j.p_morgan_trading"
    assert posts[0]["content"] == "First post"
    assert posts[0]["datetime"] == "2024-07-10T15:30:00Z"
    assert posts[0]["image"] == "https://example.com/image1.jpg"
    # Second post
    assert posts[1]["user"] == "j.p_morgan_trading"
    assert posts[1]["content"] == "Second post"
    assert posts[1]["datetime"] == "2024-07-11T14:20:00Z"
    assert posts[1]["image"] is None
