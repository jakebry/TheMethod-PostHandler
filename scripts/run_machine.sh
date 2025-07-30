#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -e

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

       # Wait for the machine to complete its natural execution
       echo "Waiting for machine to complete execution..."
       MAX_WAIT=300
       WAITED=0
       while true; do
         STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
         if [[ "$STATUS" == "stopped" ]]; then
           echo "Machine $SCRAPER_MACHINE_ID has completed execution."
           EXIT_CODE=0
           break
         fi
         if (( WAITED >= MAX_WAIT )); then
           echo "Timed out waiting for machine $SCRAPER_MACHINE_ID to complete."
           EXIT_CODE=1
           break
         fi
         sleep 5
         WAITED=$((WAITED+5))
       done
       
       # Wait longer for logs to be available (GitHub Actions needs more time)
       echo "Waiting for logs to be available..."
       sleep 45
       
       # Check the logs for success/failure messages (most recent logs)
       echo "Checking machine logs for execution results..."
       
       # Wait longer for logs to be available and retry more times
      LOGS=""
      for i in {1..8}; do
        echo "Attempt $i: Fetching logs..."
        # Prefer machine scoped logs to ensure we get output even after stop
        LOGS=$(flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --no-color --max 100 2>/dev/null || echo "")

        # Fallback to app wide logs if machine logs fail
        if [[ -z "$LOGS" ]]; then
          echo "Trying alternative log method..."
          LOGS=$(flyctl logs -a threads-scraper --instance "$SCRAPER_MACHINE_ID" --no-color --max 100 2>/dev/null || echo "")
        fi
         
         # Debug: Show what we're getting
         echo "Log length: ${#LOGS} characters"
         if [[ ${#LOGS} -gt 0 ]]; then
           echo "Last 500 chars of logs: ${LOGS: -500}"
         fi
         
         # Check if we have the expected log messages (more flexible patterns)
         if echo "$LOGS" | grep -q "Method is working" || echo "$LOGS" | grep -q "Method stopped"; then
           echo "Found execution results in logs (attempt $i)"
           break
         else
           echo "No execution results found in logs (attempt $i), waiting 20 seconds..."
           sleep 20
         fi
       done
       
       echo "Recent logs (last 100 lines):"
       echo "$LOGS"
       
       # Check for success message first (prioritize success) - more flexible patterns
       if echo "$LOGS" | grep -q "Method is working"; then
         echo "SUCCESS: Posts were successfully extracted"
         EXIT_CODE=0
       elif echo "$LOGS" | grep -q "Method stopped"; then
         echo "ERROR: No posts could be extracted"
         echo "::error::No Posts could be extracted"
         EXIT_CODE=1
       else
         echo "WARNING: Could not determine execution result from logs"
         echo "::warning::Could not determine execution result from logs"
         EXIT_CODE=0
       fi

# Stop the machine (no --wait flag)
flyctl machine stop "$SCRAPER_MACHINE_ID" -a threads-scraper
echo "Machine $SCRAPER_MACHINE_ID has been successfully stopped."

# Exit with the appropriate code
exit $EXIT_CODE
