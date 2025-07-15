from unittest.mock import patch

from src import main


def test_main_logs_start_when_posts_returned():
    with patch("src.main.load_json", return_value=[]), \
         patch("src.main.save_json"), \
         patch("src.main.deduplicate_posts", side_effect=lambda x: x), \
         patch("src.main.sort_posts_newest_first", side_effect=lambda x: x), \
         patch("src.main.scrape_threads", return_value=[{"id": "1", "user": "u", "datetime": "d", "content": "c"}]), \
         patch("src.main.log_method_start") as log_start, \
         patch("src.main.log_method_stop") as log_stop:
        main.main()
        log_start.assert_called_once()
        log_stop.assert_not_called()


def test_main_logs_stop_when_no_posts():
    with patch("src.main.load_json", return_value=[]), \
         patch("src.main.save_json"), \
         patch("src.main.deduplicate_posts", side_effect=lambda x: x), \
         patch("src.main.sort_posts_newest_first", side_effect=lambda x: x), \
         patch("src.main.scrape_threads", return_value=[]), \
         patch("src.main.log_method_start") as log_start, \
         patch("src.main.log_method_stop") as log_stop:
        main.main()
        log_stop.assert_called_once()
        log_start.assert_not_called()


def test_main_logs_stop_on_error():
    with patch("src.main.load_json", return_value=[]), \
         patch("src.main.save_json"), \
         patch("src.main.deduplicate_posts", side_effect=lambda x: x), \
         patch("src.main.sort_posts_newest_first", side_effect=lambda x: x), \
         patch("src.main.scrape_threads", side_effect=Exception("boom")), \
         patch("src.main.log_method_start") as log_start, \
         patch("src.main.log_method_stop") as log_stop:
        main.main()
        log_stop.assert_called_once()
        log_start.assert_not_called()
