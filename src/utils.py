import json
from typing import List, Dict, Any


def load_json(path: str) -> Any:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_json(path: str, data: Any) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def deduplicate_posts(posts: List[Dict]) -> List[Dict]:
    seen = set()
    unique_posts = []
    for post in posts:
        post_id = post.get('id') or (post.get('user'), post.get('datetime'), post.get('content'))
        if post_id not in seen:
            seen.add(post_id)
            unique_posts.append(post)
    return unique_posts

def sort_posts_newest_first(posts: List[Dict]) -> List[Dict]:
    return sorted(posts, key=lambda x: x.get('datetime') or '', reverse=True)
