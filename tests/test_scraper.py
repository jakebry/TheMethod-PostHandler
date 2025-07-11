from pathlib import Path
from unittest.mock import patch

from src.scraper import scrape_threads

SAMPLE_HTML = Path("tests/data/sample_source_2024_06.html").read_text()


@patch("src.scraper.update_rotation_history")
@patch("src.scraper.download_html", return_value=SAMPLE_HTML)
def test_scrape_threads(mock_download, mock_update):
    posts = scrape_threads()
    assert len(posts) == 2
    assert posts[0]["user"] == "j.p_morgan_trading"
