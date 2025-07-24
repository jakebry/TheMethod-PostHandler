import json
from src import method_tracker


def test_log_method_working_and_stopped(tmp_path, monkeypatch):
    print("Testing: Method tracking and logging")
    history_file = tmp_path / "history.json"
    monkeypatch.setattr(method_tracker, "HISTORY_PATH", str(history_file))
    times = iter([
        "2025-01-01 00:00:00 PDT",
        "2025-01-01 00:00:01 PDT",
        "2025-01-01 00:00:02 PDT",
        "2025-01-01 00:00:03 PDT",
    ])
    monkeypatch.setattr(method_tracker, "now_pacific", lambda: next(times))

    # First call should create a new working entry
    method_tracker.log_method_working()
    data = json.loads(history_file.read_text())
    assert len(data) == 1
    assert data[0]["method"] == method_tracker.METHOD_NAME
    assert data[0]["status"] == "working"
    assert data[0]["end"] is not None

    # Second call should update the end time of the existing working entry
    first_end = data[0]["end"]
    method_tracker.log_method_working()
    data = json.loads(history_file.read_text())
    assert len(data) == 1  # Still only one entry
    assert data[0]["status"] == "working"
    assert data[0]["end"] != first_end  # End time should be updated

    # Mark as stopped
    method_tracker.log_method_stopped()
    data = json.loads(history_file.read_text())
    assert data[0]["status"] == "stopped"
    assert data[0]["end"] is not None

    # Starting again should create a new entry
    method_tracker.log_method_working()
    data = json.loads(history_file.read_text())
    assert len(data) == 2  # Now we have two entries
    assert data[1]["status"] == "working"  # New entry should be working
