# Post Handler

A high-performance Threads scraper that extracts posts from trusted sources and stores them in Supabase. Built with Playwright, optimized for Fly.io deployment.

## 🎯 What It Does

- **Scrapes posts** from Threads accounts marked as "trusted sources" in Supabase
- **Stores data** in structured format with metadata
- **Handles detection** through browser fingerprinting protection
- **Tracks method effectiveness** and rotates when methods fail
- **Runs continuously** via scheduled jobs on Fly.io

## 🏗️ Architecture

```
Threads.net → Playwright → HTML Parsing → Post Extraction → Supabase Storage
```

## 🔄 Workflow

1. **Initialize**: Load environment, connect to Supabase, fetch trusted sources
2. **Scrape**: For each source, create browser session, extract posts, store data
3. **Track**: Log method success/failure in `data/threads_rotation_history.json`

## 🚀 Quick Start

### Setup
```bash
git clone <repository>
cd Threads-Scraper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment
Create `.env`:
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_USER_EMAIL=admin@example.com
SUPABASE_USER_PASSWORD=admin_password
```

### Deploy
```bash
./scripts/deploy.sh
```

## 📊 Data Structure

```json
{
  "datetime": "2024-01-15T10:30:00Z",
  "account_handle": "username",
  "platform": "Threads",
  "content": "Post content text...",
  "image": "https://...",
  "user": "username"
}
```

## 🤖 AI Development Guide

### Key Components
- **`src/main.py`**: Entry point orchestrating scraping process
- **`src/scraper.py`**: Core scraping logic and Supabase integration
- **`src/methods/method_1.py`**: Current HTML extraction method
- **`src/method_tracker.py`**: Method effectiveness tracking
- **`src/browser_manager.py`**: Playwright browser management

### Adding New Methods
1. Create `src/methods/method_N.py`
2. Implement:
   ```python
   def download_html_playwright(url, profile_name, session_name)
   def extract_posts(html)
   ```
3. Update method tracking in `src/method_tracker.py`

### Database Schema
- **trusted_sources**: `{account_handle, platform}`
- **posts**: `{datetime, account_handle, platform, content, image, user}`

## 📈 Monitoring

```bash
# Check status
./scripts/status.sh

# View logs
fly logs

# Run manually
python -m src.main
```

## 🔧 Configuration

- **Browser settings**: `src/browser_manager.py`
- **Scraping methods**: `src/methods/`
- **Performance tuning**: See `PERFORMANCE_OPTIMIZATIONS.md`

## 🛡️ Features

- **Anti-detection**: Browser fingerprinting protection, session persistence
- **Performance**: Volume mounting, pre-built binaries, optimized flags
- **Method rotation**: Automatic tracking and history logging
- **Scheduled**: Runs every 5 minutes via Fly.io jobs

## 📚 Documentation

- [Performance Optimizations](PERFORMANCE_OPTIMIZATIONS.md)
- [Fly.io Configuration](fly.toml)
- [Docker Configuration](Dockerfile)
