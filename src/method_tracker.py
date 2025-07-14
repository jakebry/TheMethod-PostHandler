import json
import os
from datetime import datetime

HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'threads_rotation_history.json')

METHOD_NAME = "Method 1: Span hierarchy"

def _load_history():
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []

def _save_history(history):
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def log_method_start():
    history = _load_history()
    now = datetime.utcnow().isoformat()
    # Check if already working
    for entry in history:
        if entry['method'] == METHOD_NAME and entry['status'] == 'working' and entry['end'] is None:
            return  # Already marked as working
    # Otherwise, add new entry
    history.append({
        'method': METHOD_NAME,
        'status': 'working',
        'start': now,
        'end': None
    })
    _save_history(history)

def log_method_stop():
    history = _load_history()
    now = datetime.utcnow().isoformat()
    updated = False
    for entry in history:
        if entry['method'] == METHOD_NAME and entry['status'] == 'working' and entry['end'] is None:
            entry['status'] = 'stopped'
            entry['end'] = now
            updated = True
    if updated:
        _save_history(history) 