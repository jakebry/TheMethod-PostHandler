# syntax=docker/dockerfile:1

# Use official Python image with latest Debian Bookworm
FROM python:3.11-slim-bookworm

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/app/.cache/playwright \
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Create a non-root user for security
RUN useradd -m appuser

# Set work directory
WORKDIR /app

# Install system dependencies (if needed for playwright, bs4, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        ca-certificates \
        libnss3 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libxss1 \
        libasound2 \
        libgbm1 \
        libxshmfence1 \
        libxcomposite1 \
        libxrandr2 \
        libu2f-udev \
        libdrm2 \
        libxdamage1 \
        libxfixes3 \
        libxext6 \
        libx11-xcb1 \
        libx11-6 \
        libxcb1 \
        libexpat1 \
        libuuid1 \
        fonts-liberation \
        libappindicator3-1 \
        lsb-release \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

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

# Install Playwright browsers and dependencies as root (before switching to appuser)
RUN python -m playwright install chromium \
    && python -m playwright install-deps chromium

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Entrypoint for the worker
CMD ["python", "-m", "src.main"] 