# Use Alpine-based Python image for better security (fewer vulnerabilities)
# Alpine uses musl libc and has a smaller attack surface
FROM python:3.12-alpine

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Create a non-root user for security (Alpine uses adduser)
RUN adduser -D -s /bin/sh appuser

# Set work directory
WORKDIR /app

# Install system dependencies for Alpine (using apk)
# Alpine has fewer vulnerabilities due to minimal nature
RUN apk update \
    && apk upgrade \
    && apk add --no-cache \
        ca-certificates \
        chromium \
        nss \
        freetype \
        freetype-dev \
        harfbuzz \
        ca-certificates \
        ttf-freefont \
        font-noto-emoji \
        wqy-zenhei \
        && rm -rf /var/cache/apk/*

# Install Python dependencies with security updates
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir --upgrade -r requirements.txt

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

# Configure Playwright to use system Chromium (Alpine package)
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH=/usr/bin/chromium-browser

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Default entrypoint - will be overridden by fly.toml for exec commands
CMD ["python", "-m", "src.main"] 