import pytest
from src.methods import method_1


def test_scrape_threads_real():
    posts = method_1.scrape_threads()
    assert isinstance(posts, list)
    assert len(posts) > 0
    first = posts[0]
    assert first.get("user")
    assert first.get("content")
    assert first.get("datetime")
