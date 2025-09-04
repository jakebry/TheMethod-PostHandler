# Use single-stage build for simplicity and reliability
FROM python:3.12-slim

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Create a non-root user for security
RUN useradd -m appuser

# Set work directory
WORKDIR /app

# Install system dependencies and apply security updates
# Include Playwright's required dependencies
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libatspi2.0-0 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libglib2.0-0 \
        libnspr4 \
        libnss3 \
        libx11-6 \
        libx11-xcb1 \
        libxcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        libxss1 \
        libcups2 \
        libcairo2 \
        libpango-1.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y

# Install Python dependencies with security updates
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --upgrade --root-user-action=ignore -r requirements.txt \
    && pip list

# Copy project files
COPY . .

# Create cache directories
RUN mkdir -p /app/.cache/playwright \
    && mkdir -p /app/.cache/browser_profiles \
    && mkdir -p /app/.cache/sessions

# Alternative approach if you still get font errors:
# Replace the install-deps line with:
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     fonts-liberation \
#     fonts-ubuntu \
#     fonts-unifont \
#     && rm -rf /var/lib/apt/lists/* \
#     && python -m playwright install chromium

# Test that all required packages are available
RUN python -c "import dotenv; import supabase; import playwright; import bs4; import requests; print('✅ All packages imported successfully')"

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Install Playwright browsers as appuser (this ensures they're in the right location)
RUN python -m playwright install chromium

# Debug: Show where browsers are installed
RUN find /app/.cache -name "*chromium*" -type d 2>/dev/null || echo "No chromium directories found"
RUN find /app/.cache -name "*chrome*" -type f 2>/dev/null || echo "No chrome executables found"

# Test that Playwright can launch a browser as appuser
RUN python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(headless=True); browser.close(); p.stop(); print('✅ Playwright browser test successful')"

# Default entrypoint - will be overridden by fly.toml for exec commands
CMD ["python", "-m", "src.main"] 