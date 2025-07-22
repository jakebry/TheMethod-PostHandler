from unittest.mock import patch

from src import main


def test_main_logs_working_when_posts_returned():
    print("Testing: Main logs working when posts are returned")
    with patch("src.main.scrape_and_store_posts", return_value=True), \
         patch("src.main.log_method_working") as log_working, \
         patch("src.main.log_method_stopped") as log_stopped:
        main.main()
        log_working.assert_called_once()
        log_stopped.assert_not_called()


def test_main_logs_stopped_when_no_posts():
    print("Testing: Main logs stopped when no posts found")
    with patch("src.main.scrape_and_store_posts", return_value=False), \
         patch("src.main.log_method_working") as log_working, \
         patch("src.main.log_method_stopped") as log_stopped:
        main.main()
        log_stopped.assert_called_once()
        log_working.assert_not_called()


def test_main_logs_stopped_on_error():
    print("Testing: Main logs stopped when scraping fails")
    with patch("src.main.scrape_and_store_posts", side_effect=Exception("boom")), \
         patch("src.main.log_method_working") as log_working, \
         patch("src.main.log_method_stopped") as log_stopped:
        main.main()
        log_stopped.assert_called_once()
        log_working.assert_not_called()
