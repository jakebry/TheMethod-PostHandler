#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -euo pipefail

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}
CMD=${1:-"python -m src.main"}

# Start the machine and wait until it's running
flyctl machine start "$MACHINE_ID" -a "$APP" --wait

# Execute the command via SSH
flyctl ssh console -a "$APP" -s "$MACHINE_ID" -C "$CMD"

# Stop the machine and wait until it is fully stopped
flyctl machine stop "$MACHINE_ID" -a "$APP" --wait
