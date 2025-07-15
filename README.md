# Does not work
# Threads Scraper

A robust, industry-standard Python project for scraping public posts from Threads user profiles (e.g., `j.p_morgan_trading`) without logging in. The scraper is designed to adapt to changes in Threads' HTML structure, version its scraping methods, and keep a history of which method works for which date range.

## Features
- Scrapes Threads user posts (content, date/time, user, image link, likes, comments) without login
- Saves posts to `data/posts.json` (newest first, no duplicates)
- Tracks scraping method versions in `data/threads_rotation_history.json`
- Detects and logs when Threads changes their HTML structure
- Modular, extensible, and fully unit-tested

## Project Structure
```
Threads Scraper/
  ├── src/
  │   ├── main.py                # Entry point
  │   ├── methods/               # Scraping methods (e.g., method_1.py)
  │   ├── utils.py               # Utilities (JSON, deduplication, etc.)
  │   ├── config.py              # Configurations
  │   └── method_tracker.py      # Tracks method working periods
  ├── tests/                     # Unit tests
  ├── data/
  │   ├── posts.json             # Scraped posts
  │   └── threads_rotation_history.json # Scraper method history
  ├── new_source_code.html       # For saving new/unknown HTML
  ├── requirements.txt           # Dependencies
  └── README.md
```

## Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scraper:
   ```bash
   python src/main.py
   ```
3. Inspect `data/posts.json` for results.

## How Method Tracking Works
- The current scraping logic is in `src/methods/method_1.py` ("Method 1: Span hierarchy").
- The system automatically logs when a method starts or stops working in `data/threads_rotation_history.json`.
- If scraping fails (no posts parsed or an error), the method is marked as stopped.

## Adding New Scraping Methods
- Add a new file in `src/methods/` (e.g., `method_2.py`).
- Update `src/main.py` to import and use the new method.
- The method tracker will automatically log the new method's working period.

## Testing
Run all tests with:
```bash
pytest tests/
```

---

**Note:** If scraping fails, the HTML will be saved to `new_source_code.html` for inspection and method update.
