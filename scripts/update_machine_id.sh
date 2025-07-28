#!/bin/bash

# Script to update machine ID in GitHub Actions workflow
# This script helps manage machine ID updates when Fly.io machines are recreated

set -e

echo "🔧 Updating Machine ID in GitHub Actions Workflow"
echo "================================================"

# Get current machine ID (handle both started and stopped machines)
echo "📱 Getting current machine ID..."
CURRENT_MACHINE_ID=$(fly status --json | jq -r '.Machines[0].ID // empty' 2>/dev/null || echo "")

if [ -z "$CURRENT_MACHINE_ID" ] || [ "$CURRENT_MACHINE_ID" = "null" ]; then
    echo "❌ Error: Could not get current machine ID"
    echo "Please ensure you have at least one machine:"
    echo "  fly status"
    echo "  fly machine start <MACHINE_ID>"
    exit 1
fi

echo "✅ Current machine ID: $CURRENT_MACHINE_ID"

# Update the GitHub Actions workflow file
WORKFLOW_FILE=".github/workflows/scheduled-scrape.yml"

if [ ! -f "$WORKFLOW_FILE" ]; then
    echo "❌ Error: Workflow file not found: $WORKFLOW_FILE"
    exit 1
fi

echo "📝 Updating workflow file..."

# Create backup
cp "$WORKFLOW_FILE" "$WORKFLOW_FILE.backup"

# Update the machine ID in the workflow file
sed -i.bak "s/SCRAPER_MACHINE_ID: \"[^\"]*\"/SCRAPER_MACHINE_ID: \"$CURRENT_MACHINE_ID\"/" "$WORKFLOW_FILE"

# Remove backup file created by sed
rm -f "$WORKFLOW_FILE.bak"

echo "✅ Updated machine ID in $WORKFLOW_FILE"
echo ""
echo "📋 Changes made:"
echo "  • Updated SCRAPER_MACHINE_ID to: $CURRENT_MACHINE_ID"
echo ""
echo "🚀 Next steps:"
echo "  • Commit the changes: git add .github/workflows/scheduled-scrape.yml"
echo "  • Push to trigger the updated workflow"
echo ""
echo "📊 To verify the update:"
echo "  • Check the workflow file: cat $WORKFLOW_FILE"
echo "  • Test the machine: fly machine start $CURRENT_MACHINE_ID" 