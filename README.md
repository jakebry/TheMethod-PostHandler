# Threads Scraper

A Python-based scraper for extracting posts and media from Threads.net profiles. This tool uses Selenium and BeautifulSoup to navigate and parse Threads content, saving posts and images to both text and Excel formats.

## Features

- 🔐 Secure login using Instagram credentials
- 📝 Extracts comprehensive post data:
  - Post content
  - Timestamps
  - Like counts
  - Comment counts
  - Images (with automatic download)
- 💾 Multiple output formats:
  - Text file with detailed post information
  - Excel file with embedded images
- 🛡️ Anti-detection measures:
  - Undetected ChromeDriver
  - Random delays between actions
  - Smart scrolling behavior
- 🔄 Duplicate post detection
- 📸 Automatic image downloading and management
- 📊 Excel export with embedded images

## Requirements

- Python 3.7+
- Chrome browser installed
- Required packages (install using `pip install -r requirements.txt`):
  - undetected-chromedriver
  - selenium
  - beautifulsoup4
  - python-dotenv
  - openpyxl
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

4. Create a `.env` file in the project root with your Instagram credentials:
   ```
   THREADS_USERNAME=your_instagram_username
   THREADS_PASSWORD=your_instagram_password
   ```

## Usage

1. Ensure your `.env` file is properly configured with your Instagram credentials.

2. Run the scraper:
   ```bash
   python threads_scraper_updated.py
   ```

3. The script will:
   - Log in to Threads using your Instagram credentials
   - Navigate to the specified profile
   - Scroll through and collect posts
   - Download images
   - Save data to both text and Excel formats

## Output Files

The script generates two main output files for each profile:

1. `<username>_posts.txt`:
   - Contains detailed post information
   - Includes timestamps, likes, comments, and image URLs
   - Human-readable format

2. `<username>_posts.xlsx`:
   - Excel spreadsheet with all post data
   - Embedded images in cells
   - Organized columns for easy viewing

## Project Structure

```
threads-scraper/
├── threads_scraper_updated.py  # Main scraper script
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (not in repo)
├── images/                    # Downloaded images directory
└── README.md                  # This file
```

## Error Handling

The scraper includes robust error handling for:
- Login failures
- Network issues
- Missing elements
- Rate limiting
- Image download failures

## Limitations

- Requires Instagram login credentials
- May be affected by Threads' anti-scraping measures
- Performance depends on network speed and server response times
- Image downloading may be rate-limited

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