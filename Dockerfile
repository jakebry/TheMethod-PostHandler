# Multi-stage build for better security and smaller final image
# Stage 1: Build dependencies
FROM python:3.12-slim as builder

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime image
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

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

# Install Playwright and Chromium browser
RUN python -m playwright install chromium

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Default entrypoint - will be overridden by fly.toml for exec commands
CMD ["python", "-m", "src.main"] 