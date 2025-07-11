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
threads_scraper/
  ├── src/
  │   ├── main.py                # Entry point
  │   ├── scraper.py             # Scraper orchestration
  │   ├── methods/               # Scraping methods by version
  │   ├── utils.py               # Utilities (JSON, deduplication, etc.)
  │   └── config.py              # Configurations
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

## Adding New Scraping Methods
- Add a new file in `src/methods/` (e.g., `method_YYYY_MM.py`)
- Update `threads_rotation_history.json` with the new method and date range
- Update `src/scraper.py` to use the new method

## Testing
Run all tests with:
```bash
pytest tests/
```

---

**Note:** If scraping fails, the HTML will be saved to `new_source_code.html` for inspection and method update.
