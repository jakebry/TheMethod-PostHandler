# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based Threads scraper that extracts posts from trusted sources and stores them in Supabase. The application runs continuously on Fly.io with performance optimizations for browser automation and anti-detection measures.

## Common Development Commands

### Development Setup
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running the Application
```bash
# Run main scraper
python -m src.main

# Run specific tests
pytest tests/test_method1.py
pytest tests/test_method_tracker.py
pytest tests/test_utils.py
pytest tests/test_main.py

# Run all tests
pytest tests/
```

### Deployment
```bash
# Deploy to Fly.io (includes volume setup)
./scripts/deploy.sh

# Check application status
./scripts/status.sh

# View logs
fly logs
fly logs --follow
```

## Architecture Overview

### Core Components
- **`src/main.py`**: Entry point that orchestrates the scraping process and handles method tracking
- **`src/scraper.py`**: Core scraping logic with Supabase integration and authentication
- **`src/methods/method_1.py`**: Current HTML extraction method using Playwright and BeautifulSoup
- **`src/method_tracker.py`**: Tracks method effectiveness and rotation history in `data/threads_rotation_history.json`
- **`src/browser_manager.py`**: Optimized Playwright browser management with session persistence
- **`src/performance_monitor.py`**: Performance monitoring and metrics collection

### Data Flow
1. Load trusted sources from Supabase `trusted_sources` table
2. For each source, create browser session with profile persistence
3. Extract posts using current method (method_1.py)
4. Store posts in Supabase `user_posts` table
5. Track method success/failure in rotation history

### Method System
The application uses a method rotation system where different scraping approaches can be implemented:
- Each method implements `download_html_playwright()` and `extract_posts()` functions
- Method effectiveness is tracked in `data/threads_rotation_history.json`
- Failed methods are marked as "stopped", working methods update their "end" time

### Browser Optimization
- **Session Persistence**: Browser profiles and cookies saved/restored between runs
- **Anti-Detection**: Randomized delays, viewport sizes, user agents, and stealth measures
- **Performance**: Volume mounting on Fly.io for browser cache persistence
- **Resource Management**: Proper cleanup and browser reuse

## Environment Configuration

Required environment variables in `.env`:
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_USER_EMAIL=admin@example.com
SUPABASE_USER_PASSWORD=admin_password
```

## Database Schema

### Tables
- **`trusted_sources`**: Contains `{account_handle, platform}` for accounts to scrape
- **`user_posts`**: Stores extracted posts with `{datetime, account_handle, platform, content, image}`

## Fly.io Configuration

- Runs as scheduled job every 5 minutes
- Uses volume mounting for browser profile persistence
- Performance-optimized with 2GB memory and performance CPU
- Environment variables set for Playwright browser path optimization

## Testing

Tests are organized by component:
- `test_method1.py`: Tests HTML extraction and post parsing
- `test_method_tracker.py`: Tests method rotation and history tracking
- `test_utils.py`: Tests utility functions
- `test_main.py`: Tests main application flow

All tests use pytest with fixtures defined in `conftest.py`.

## Performance Monitoring

The application includes built-in performance monitoring:
- Browser launch times
- Page load times  
- Session restoration times
- Overall scraping duration

Access via `src.performance_monitor.get_performance_monitor()`.