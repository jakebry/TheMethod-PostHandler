import os
import json
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from threads_scraper import extract_posts
from threads_scraper_supabase import ThreadsScraper

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
                                            {"url": "https://example.com/img1.jpg"}
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


def build_scraper(mock_supabase):
    os.environ['THREADS_USERNAME'] = 'user'
    os.environ['THREADS_PASSWORD'] = 'pass'
    os.environ['SUPABASE_URL'] = 'http://supabase'
    os.environ['SUPABASE_KEY'] = 'key'
    with patch.object(ThreadsScraper, '_setup_driver'):
        with patch('threads_scraper_supabase.create_client', return_value=mock_supabase) as mocked:
            scraper = ThreadsScraper()
    return scraper, mocked


def test_pipeline_parses_and_uploads():
    html = f'<html><body><script type="application/json">{json.dumps(SAMPLE_JSON)}</script></body></html>'
    soup = BeautifulSoup(html, 'html.parser')
    posts = extract_posts(soup)
    assert posts

    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_supabase.table.return_value = mock_table

    scraper, mocked_create = build_scraper(mock_supabase)

    scraper._save_to_supabase(posts, 'user')

    mocked_create.assert_called_once_with('http://supabase', 'key')
    mock_supabase.table.assert_called_once_with('posts')
    mock_table.insert.assert_called_once()
    args, kwargs = mock_table.insert.call_args
    assert args[0][0]['author'] == 'user'
    mock_insert.execute.assert_called_once()
