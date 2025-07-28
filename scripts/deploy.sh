#!/bin/bash

# Deployment script for Threads Scraper with optimized browser performance
# This script sets up volumes and deploys the application

set -e

echo "🚀 Deploying Threads Scraper with optimized browser performance..."

# Check if we're in the right directory
if [ ! -f "fly.toml" ]; then
    echo "❌ Error: fly.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if volume exists, create if not
echo "📦 Checking for browser cache volume..."
if ! fly volumes list | grep -q "browser_cache"; then
    echo "Creating browser cache volume..."
    fly volumes create browser_cache --size 1 --region sea
    echo "✅ Volume created successfully!"
else
    echo "✅ Volume already exists!"
fi

# Build and deploy
echo "🔨 Building and deploying application..."
fly deploy

echo "✅ Deployment completed!"
echo ""
echo "📊 Performance optimizations enabled:"
echo "  • Browser profile persistence"
echo "  • Session cookie restoration"
echo "  • Optimized browser flags"
echo "  • Anti-detection measures"
echo "  • Performance monitoring"
echo ""
echo "🔍 Monitor performance with: fly logs"
echo "📈 Check volume status with: fly volumes list" 