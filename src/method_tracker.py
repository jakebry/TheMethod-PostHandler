import json
import os
from datetime import datetime, UTC

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

def log_method_working():
    """
    Updates the current working method's end time to now.
    If no method is currently working, creates a new entry.
    """
    history = _load_history()
    now = datetime.now(UTC).isoformat()
    
    # Check if current method is already working
    for entry in history:
        if entry['method'] == METHOD_NAME and entry['status'] == 'working':
            # Update the end time to now (method is still working)
            entry['end'] = now
            _save_history(history)
            return
    
    # If no current method is working, create a new entry
    history.append({
        'method': METHOD_NAME,
        'status': 'working',
        'start': now,
        'end': now
    })
    _save_history(history)

def log_method_stopped():
    """
    Marks the current method as stopped if it was working.
    Only call this when the method actually fails.
    """
    history = _load_history()
    now = datetime.now(UTC).isoformat()
    
    for entry in history:
        if entry['method'] == METHOD_NAME and entry['status'] == 'working':
            entry['status'] = 'stopped'
            entry['end'] = now
            _save_history(history)
            return

def get_current_working_method():
    """
    Returns the currently working method entry, or None if no method is working.
    """
    history = _load_history()
    for entry in history:
        if entry['status'] == 'working':
            return entry
    return None 