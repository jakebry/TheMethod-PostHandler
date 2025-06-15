# Threads Scraper

This project scrapes posts from Threads profiles using Selenium and BeautifulSoup.

## Main Script

The main script is now `threads_scraper_updated.py`. All scraping and parsing logic is contained in this file.

## Features

- Fetches all posts from a given Threads username
- Extracts post text, timestamp, likes, replies, and reposts
- Saves data in JSON format
- Uses rotating user agents to avoid blocking
- Handles errors gracefully

## Requirements

- Python 3.7+
- Required packages (install using `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - python-dotenv
  - fake-useragent

## Installation

1. Clone this repository
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scraper:
   ```bash
   python threads_scraper_updated.py
   ```
   You will be prompted for a Threads username (without the @).

3. Output:
   - Posts are saved to `<username>_posts.txt`.
   - Logs are written to `threads_scraper.log` and `threads_scraper.debug.log`.

## Output Format

The script generates a JSON file with the following structure for each post:
```json
{
  "text": "Post content",
  "timestamp": "2024-03-21T12:34:56Z",
  "likes": 123,
  "replies": 45,
  "reposts": 67
}
```

## Notes

- The project is now based around `threads_scraper_updated.py`. The old `threads_scraper.py` is deprecated and can be deleted.
- Make sure you have Chrome installed for Selenium to work.
- The script uses rotating user agents to avoid being blocked
- Rate limiting is implemented to be respectful to Threads' servers
- Make sure you comply with Threads' terms of service and robots.txt when using this scraper

## Disclaimer

This tool is for educational purposes only. Make sure to respect Threads' terms of service and robots.txt when using this scraper. The developers are not responsible for any misuse of this tool. 