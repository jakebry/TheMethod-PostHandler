import os
import tempfile
import json
from src.utils import load_json, save_json, deduplicate_posts, sort_posts_newest_first

def test_load_and_save_json():
    data = [{"a": 1}]
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        save_json(tf.name, data)
        loaded = load_json(tf.name)
    assert loaded == data
    os.remove(tf.name)

def test_deduplicate_posts():
    posts = [
        {"id": 1, "content": "A"},
        {"id": 1, "content": "A"},
        {"id": 2, "content": "B"},
    ]
    unique = deduplicate_posts(posts)
    assert len(unique) == 2

def test_sort_posts_newest_first():
    posts = [
        {"datetime": "2024-06-01T12:00:00", "content": "A"},
        {"datetime": "2024-06-02T12:00:00", "content": "B"},
    ]
    sorted_posts = sort_posts_newest_first(posts)
    assert sorted_posts[0]["content"] == "B"
