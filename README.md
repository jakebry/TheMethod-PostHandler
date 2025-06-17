# Threads Scraper

A minimal scraper for collecting posts from public Threads.net profiles. It uses
Selenium and BeautifulSoup to parse JSON data embedded in the page and saves
the results to simple text and JSON files.

## Features

- Extracts post text, timestamps and image URLs
- Runs headless using Selenium and Chrome
- Saves results in `<username>_threads.txt` and `<username>_threads.json`
- Dumps raw page HTML and JSON blocks for debugging

## Requirements

- Python 3.7+
- Chrome browser installed
- Required packages (install using `pip install -r requirements.txt`):
  - selenium
  - beautifulsoup4
  - undetected-chromedriver
  - requests

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/threads-scraper.git
   cd threads-scraper
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Adjust the `TARGET_USER` constant in `threads_scraper_final.py` to the profile you want to scrape.

2. Run the scraper:
   ```bash
   python threads_scraper_final.py
   ```

3. The script will load the profile, scroll to the bottom of the page and extract posts into text and JSON files.

## Output Files

The scraper creates two files for each profile:

1. `<username>_threads.txt`
2. `<username>_threads.json`

## Web Viewer

You can view the scraped posts in a small web interface powered by Node and React.

1. Install Node dependencies:
   ```bash
   npm install
   ```
2. Run the scraper to generate `<username>_threads.json`:
   ```bash
   python threads_scraper_final.py
   ```
3. Start the server:
   ```bash
   npm start
   ```
4. Open `http://localhost:3000` in your browser to see the posts listed.


## Project Structure

```
threads-scraper/
├── threads_scraper_final.py   # Main scraper script
├── threads_scraper_debug.py   # Helper for inspecting page data
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Error Handling

The scraper includes basic error handling for:
- Network issues
- Missing elements
- Rate limiting

## Limitations

- May be affected by Threads' anti-scraping measures
- Performance depends on network speed and server response times

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational purposes only. Users are responsible for:
- Complying with Threads' terms of service
- Respecting rate limits and robots.txt
- Using the tool responsibly and ethically
- Not violating any privacy or data protection laws

The developers are not responsible for any misuse of this tool or any consequences resulting from its use.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 