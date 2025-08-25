# The Method – Post Handler

High-performance Threads scraper that extracts posts from trusted sources and stores them in Supabase. Built with Playwright and optimized for Fly.io.

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

1. Initialize: Load environment, connect to Supabase, fetch trusted sources
2. Scrape: For each source, create browser session, extract posts, store data
3. Track: Log method success/failure in `data/threads_rotation_history.json`

## 🚀 Quick Start

### Setup
```bash
git clone <repository>
cd TheMethod-PostHandler
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Environment
Create `.env` (use the example below and never commit real secrets):
```bash
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_USER_EMAIL=admin@example.com
SUPABASE_USER_PASSWORD=admin_password
# Optional for local testing only; production uses DB trusted_sources
THREADS_USER=example_user
```

**Note**: The `SUPABASE_SERVICE_ROLE_KEY` is required for database trigger authentication. This key is automatically set in the database session before scraping begins to ensure proper authentication for edge function calls.

### Deploy
```bash
# Set up Fly.io secrets (one-time setup)
./scripts/setup_secrets.sh

# Deploy the application
./scripts/deploy.sh
```

### GitHub Actions Setup
For automated deployment and scheduled scraping, ensure these secrets are set in your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `FLY_API_TOKEN`: Your Fly.io API token
   - `SCRAPER_MACHINE_ID`: The machine ID for your Fly.io app
   - `SUPABASE_SERVICE_ROLE_KEY`: Your Supabase service role key

The GitHub Actions workflow will automatically run the scraper every 5 minutes and handle service role key authentication.

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
- **`src/service_role_setup.py`**: Service role key initialization for database triggers
- **`src/methods/method_1.py`**: Current HTML extraction method
- **`src/method_tracker.py`**: Method effectiveness tracking
- **`src/browser_manager.py`**: Playwright browser management
- **`src/performance_monitor.py`**: Performance monitoring and metrics

### Adding New Methods
1. Create `src/methods/method_N.py`
2. Implement:
   ```python
   def download_html_playwright(url, profile_name, session_name)
   def extract_posts(html)
   ```
3. Update method tracking in `src/method_tracker.py`

### Database Schema
- trusted_sources: `{account_handle, platform}`
- user_posts: `{datetime, account_handle, platform, content, image}`

## 📈 Monitoring

```bash
# Check status
./scripts/status.sh

# View logs
fly logs
fly logs --follow

# Run manually
python -m src.main

# Test service role setup (standalone)
python3 scripts/setup_service_role.py
```

## ⚡ Performance Optimizations

### Browser Performance
- **Volume Mounting**: Persistent browser cache on Fly.io (`/app/.cache`)
- **Session Persistence**: Browser profiles and cookies saved/restored between runs
- **Pre-built Binaries**: Chromium pre-installed in Docker container
- **Optimized Flags**: Disabled unnecessary features, memory optimizations

### Key Browser Flags
```bash
# Performance flags
--disable-dev-shm-usage
--disable-gpu
--memory-pressure-off
--max_old_space_size=4096

# Anti-detection flags
--disable-blink-features=AutomationControlled
--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36
```

### Anti-Detection
- **WebDriver Masking**: `navigator.webdriver = undefined`
- **Plugin Spoofing**: Fake plugin arrays and Chrome runtime objects
- **Human-like Behavior**: Randomized delays, viewport sizes, realistic user agents
- **Session Management**: Profile isolation per account, cookie preservation

### Performance Monitoring
```python
from src.performance_monitor import get_performance_monitor

monitor = get_performance_monitor()
monitor.log_performance_summary()
```

**Metrics Tracked:**
- Browser launch time
- Page load time
- Session restoration time
- Overall scraping duration

### Expected Performance Gains
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Browser Startup | 15-30s | 5-10s | 50-75% |
| Session Restoration | N/A | 1-2s | New feature |
| Cold Page Load | 10-20s | 3-8s | 60-70% |
| Memory Usage | High | Optimized | 30-40% |

## 🔧 Configuration
- Browser settings: `src/browser_manager.py`
- Scraping methods: `src/methods/`
- Performance tuning: See browser flags above

### Environment Variables
```toml
[env]
PLAYWRIGHT_BROWSERS_PATH = '/app/.cache/playwright'
PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '0'
```

### Volume Setup
```bash
# Create volume for browser caching
fly volumes create browser_cache --size 1 --region sea

# Deploy with volume mounting
fly deploy
```

### Volume Configuration
```toml
[[mounts]]
source = "browser_cache"
destination = "/app/.cache"
```

## 🛡️ Features
- Anti-detection: Browser fingerprinting protection, session persistence
- Performance: Volume mounting, pre-built binaries, optimized flags
- Method rotation: Automatic tracking and history logging
- Scheduled: Runs every 5 minutes via Fly.io jobs

## 📝 Usage Examples

### Basic Scraping
```python
from src.methods.method_1 import download_html_playwright

# Uses optimized browser manager automatically
html = download_html_playwright("https://www.threads.net/@username")
```

### With Session Management
```python
# Session will be automatically saved and restored
html = download_html_playwright(
    "https://www.threads.net/@username",
    profile_name="my_profile",
    session_name="my_session"
)
```

## 🔍 Troubleshooting

### Volume Issues
```bash
# Check volume status
fly volumes list

# Recreate volume if needed
fly volumes destroy browser_cache
fly volumes create browser_cache --size 1 --region sea
```

### Performance Issues
```bash
# Check logs for performance metrics
fly logs

# Monitor real-time performance
fly logs --follow
```

### Browser Issues
```bash
# Rebuild with fresh browser binaries
fly deploy --no-cache
```

### Service Role Key Issues
```bash
# Check if secrets are set correctly
flyctl secrets list

# Re-set secrets if needed
./scripts/setup_secrets.sh

# Test service role setup locally
python3 scripts/setup_service_role.py
```

## 📚 Best Practices

1. **Regular Monitoring**: Check performance metrics weekly
2. **Session Cleanup**: Clear old sessions periodically
3. **Volume Management**: Monitor volume usage and resize if needed
4. **Error Handling**: Implement graceful fallbacks for browser failures
5. **Rate Limiting**: Respect Threads rate limits to avoid detection

## 📚 Documentation
- [Fly.io Configuration](fly.toml) - Deployment configuration
- [Docker Configuration](Dockerfile) - Container setup

## Security
- Do not commit `.env` or secrets. Use GitHub Actions secrets for deployment (`FLY_API_TOKEN`, `SCRAPER_MACHINE_ID`).
- Machine ID is referenced via secret in `.github/workflows/scheduled-scrape.yml`.

## License
MIT
