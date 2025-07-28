#!/bin/bash

# Script to set up Fly.io volume for browser caching
# This script creates a volume for persistent browser profiles and cache

set -e

echo "Setting up Fly.io volume for browser caching..."

# Create the volume
echo "Creating volume 'browser_cache'..."
fly volumes create browser_cache --size 1 --region sea

echo "Volume created successfully!"
echo ""
echo "Next steps:"
echo "1. Deploy your app: fly deploy"
echo "2. The volume will be automatically mounted at /app/.cache"
echo "3. Browser profiles and sessions will persist between deployments"
echo ""
echo "To check volume status: fly volumes list" 