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

# Check if we have existing machines and their status
echo "🔍 Checking for existing machines..."
EXISTING_MACHINES=$(fly machines list --json | jq -r '.[].id' | wc -l)

if [ "$EXISTING_MACHINES" -gt 0 ]; then
    echo "✅ Found $EXISTING_MACHINES existing machine(s)"
    
    # Check if any machines are stopped
    STOPPED_MACHINES=$(fly machines list --json | jq -r '.[] | select(.state == "stopped") | .id' | wc -l)
    
    if [ "$STOPPED_MACHINES" -gt 0 ]; then
        echo "⚠️  Found $STOPPED_MACHINES stopped machine(s)"
        echo "🔄 Starting stopped machines before deployment..."
        
        # Start all stopped machines
        fly machines list --json | jq -r '.[] | select(.state == "stopped") | .id' | while read -r machine_id; do
            echo "🚀 Starting machine: $machine_id"
            fly machine start "$machine_id"
        done
        
        # Wait a moment for machines to start
        sleep 5
    fi
    
    echo "🔄 Deploying to existing machines..."
    # Use --ha=false to prevent creating new machines
    fly deploy --ha=false
else
    echo "🆕 No existing machines found, creating new deployment..."
    fly deploy
fi

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