# Threads Scraper

A high-performance Threads scraper optimized for Fly.io deployment with browser session persistence and anti-detection measures.

## 🚀 Features

- **Optimized Browser Performance**: 50-75% faster startup times
- **Session Persistence**: Browser profiles and cookies persist between runs
- **Anti-Detection Measures**: Advanced browser fingerprinting protection
- **Performance Monitoring**: Built-in metrics and monitoring
- **Fly.io Optimized**: Volume mounting and pre-built browser binaries

## 📊 Performance Optimizations

This scraper implements the recommended best practices for browser performance on Fly.io:

- **Volume Mounting**: Persistent browser cache storage
- **Pre-built Binaries**: Chromium browser pre-installed in Docker
- **Session Management**: Automatic cookie and storage state restoration
- **Optimized Flags**: 50+ performance and anti-detection browser flags
- **Performance Monitoring**: Real-time metrics tracking

See [PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md) for detailed documentation.

## 🛠️ Machine ID Management

When Fly.io machines are recreated (e.g., after deployments), the machine ID changes. To update the scheduled scraping:

### Automatic Update
```bash
./scripts/update_machine_id.sh
```

### Manual Update
1. Get current machine ID: `fly status`
2. Update `.github/workflows/scheduled-scrape.yml`
3. Commit and push changes

## 📋 Deployment

### Quick Deploy
```bash
./scripts/deploy.sh
```

### Manual Setup
```bash
# Create volume
fly volumes create browser_cache --size 1 --region sea

# Deploy
fly deploy
```

## 📈 Monitoring

### Check Status
```bash
./scripts/status.sh
```

### View Logs
```bash
fly logs
```

### Performance Metrics
Look for "browser_launch" timing in logs to see optimization effectiveness.

## 🔧 Configuration

### Environment Variables
- `FLY_API_TOKEN`: Fly.io API token for GitHub Actions
- `SCRAPER_MACHINE_ID`: Current machine ID (auto-updated)

### Volume Configuration
- `browser_cache`: 1GB volume for browser profiles and cache

## 📝 Usage

The scraper runs automatically every 5 minutes via GitHub Actions, or manually:

```bash
# Start machine and run scraper
./scripts/run_machine.sh

# Check status
fly status

# View logs
fly logs
```

## 🎯 Expected Performance Gains

- **Browser startup**: 50-75% faster (15-30s → 5-10s)
- **Page loading**: 60-70% faster (10-20s → 3-8s)
- **Memory usage**: 30-40% reduction
- **Session restoration**: 1-2s vs cold start

## 🛡️ Anti-Detection Features

- Browser fingerprinting protection
- Session management with profile isolation
- Human-like interaction patterns
- Optimized HTTP headers and user agents

## 📚 Documentation

- [Performance Optimizations](PERFORMANCE_OPTIMIZATIONS.md) - Detailed optimization guide
- [Fly.io Configuration](fly.toml) - Deployment configuration
- [Docker Configuration](Dockerfile) - Container optimization
