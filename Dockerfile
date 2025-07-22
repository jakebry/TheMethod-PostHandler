# syntax=docker/dockerfile:1

# Use official Python image
FROM python:3.11-slim

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

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

# Set permissions
RUN chown -R appuser:appuser /app
USER appuser

# Install Playwright browsers as appuser (no --with-deps)
RUN python -m playwright install

# Entrypoint for the worker
CMD ["python", "-m", "src.main"] 