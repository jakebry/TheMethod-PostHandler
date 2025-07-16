import json
from src import method_tracker


def test_log_method_start_and_stop(tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr(method_tracker, "HISTORY_PATH", str(history_file))

    method_tracker.log_method_start()
    data = json.loads(history_file.read_text())
    assert len(data) == 1
    assert data[0]["method"] == method_tracker.METHOD_NAME
    assert data[0]["status"] == "working"
    assert data[0]["end"] is None

    # calling start again should not add a new entry
    method_tracker.log_method_start()
    data = json.loads(history_file.read_text())
    assert len(data) == 1

    method_tracker.log_method_stop()
    data = json.loads(history_file.read_text())
    assert data[0]["status"] == "stopped"
    assert data[0]["end"] is not None
