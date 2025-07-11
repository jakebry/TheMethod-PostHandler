import pytest
from unittest.mock import patch
from src.scraper import scrape_threads

@patch('src.scraper.download_html', return_value='<html></html>')
@patch('src.scraper.scrape_posts_from_html', return_value=[{"content": "Test", "datetime": "2024-06-01T12:00:00", "user": "j.p_morgan_trading", "image": None, "likes": 10, "comments": 2}])
def test_scrape_threads(mock_scrape, mock_download):
    posts = scrape_threads()
    assert isinstance(posts, list)
    assert posts[0]["content"] == "Test"
