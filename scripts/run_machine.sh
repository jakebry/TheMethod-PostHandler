#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -euo pipefail

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}
CMD=${1:-"python -m src.main"}

# Start the machine
flyctl machine start "$SCRAPER_MACHINE_ID" -a threads-scraper

# Smarter wait loop: poll until the machine is started (max 30 seconds)
MAX_WAIT=30
WAITED=0
while true; do
  STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
  if [[ "$STATUS" == "started" ]]; then
    echo "Machine $SCRAPER_MACHINE_ID is started."
    break
  fi
  if (( WAITED >= MAX_WAIT )); then
    echo "Timed out waiting for machine $SCRAPER_MACHINE_ID to start."
    exit 1
  fi
  sleep 2
  WAITED=$((WAITED+2))
done

echo "Waiting a few more seconds for DNS propagation..."
sleep 5

# Retry logic for exec
MAX_RETRIES=3
RETRY=0
while (( RETRY < MAX_RETRIES )); do
  set +e
  flyctl machines exec "$SCRAPER_MACHINE_ID" -a threads-scraper -- "python -m src.main"
  EXIT_CODE=$?
  set -e
  if [[ $EXIT_CODE -eq 0 ]]; then
    echo "Exec succeeded."
    break
  else
    echo "Exec failed (attempt $((RETRY+1))/$MAX_RETRIES)."
    if (( RETRY == MAX_RETRIES - 1 )); then
      echo "Giving up after $MAX_RETRIES attempts."
      exit $EXIT_CODE
    fi
    echo "Retrying in 5 seconds..."
    sleep 5
    RETRY=$((RETRY+1))
  fi
done

# Stop the machine and wait until it is fully stopped
flyctl machine stop "$MACHINE_ID" -a "$APP" --wait
