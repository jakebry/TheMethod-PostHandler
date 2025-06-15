# Threads Profile Scraper

A Python-based web scraper that retrieves posts and post data from Threads.net profiles.

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

Run the script:
```bash
python threads_scraper.py
```

When prompted, enter the Threads username (without the @ symbol) that you want to scrape.

The script will:
1. Fetch all posts from the specified profile
2. Display the posts in the console
3. Save the posts to a JSON file named `{username}_posts.json`

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

- The script uses rotating user agents to avoid being blocked
- Rate limiting is implemented to be respectful to Threads' servers
- Make sure you comply with Threads' terms of service and robots.txt when using this scraper

## Disclaimer

This tool is for educational purposes only. Make sure to respect Threads' terms of service and robots.txt when using this scraper. The developers are not responsible for any misuse of this tool. 