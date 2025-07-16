from pathlib import Path
from unittest.mock import patch
from bs4 import BeautifulSoup

from src.methods import method_1

SAMPLE_HTML = Path("tests/data/sample_source_2024_06.html").read_text()
NESTED_HTML = Path("tests/data/nested_post.html").read_text()



def test_extract_posts_from_json():
    posts = method_1.extract_posts(SAMPLE_HTML)
    assert len(posts) == 2
    assert posts[0]["user"] == "j.p_morgan_trading"
    assert posts[0]["content"] == "First post"
    assert posts[0]["datetime"] == "2024-07-10T15:30:00Z"
    assert posts[0]["image"] == "https://example.com/image1.jpg"
    assert posts[1]["image"] is None


def test_extract_posts_nested_html():
    posts = method_1.extract_posts(NESTED_HTML)
    assert len(posts) == 2
    assert posts[0]["user"] == "j.p_morgan_trading"
    assert posts[0]["content"].startswith("🟢Buy")
    assert posts[0]["datetime"] == "2025-06-16T08:55:01.000Z"
    assert posts[0]["image"] is not None
    assert posts[1]["content"].startswith("SL: 0.789")
    assert posts[1]["datetime"] == "2025-06-16T08:56:30.000Z"


@patch("src.methods.method_1.download_html_playwright", return_value=SAMPLE_HTML)
def test_scrape_threads_uses_downloader(mock_download):
    posts = method_1.scrape_threads()
    mock_download.assert_called_once()
    assert len(posts) == 2
