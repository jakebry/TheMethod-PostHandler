#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -e

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}
CMD=${1:-"python -m src.main"}
# Window (in seconds) after machine start to consider logs relevant for this run
LOG_WINDOW_SECONDS=${LOG_WINDOW_SECONDS:-120}

# Convert RFC3339/ISO8601 timestamp to epoch seconds (GNU date on Linux, BSD date on macOS)
to_epoch() {
  TS_RAW="$1"
  # Normalize by removing fractional seconds if present (e.g., 2025-01-01T00:00:00.123Z -> 2025-01-01T00:00:00Z)
  TS_NANO_STRIPPED=$(printf "%s" "$TS_RAW" | sed -E 's/([0-9]{2}:[0-9]{2}:[0-9]{2})(\.[0-9]+)?Z/\1Z/')
  # Prefer GNU date (Linux, GitHub Actions)
  if date -u -d "$TS_NANO_STRIPPED" +%s >/dev/null 2>&1; then
    date -u -d "$TS_NANO_STRIPPED" +%s
    return
  fi
  # Fallback for BSD date (macOS)
  if command -v gdate >/dev/null 2>&1; then
    gdate -u -d "$TS_NANO_STRIPPED" +%s
    return
  fi
  # BSD date requires explicit format. Ensure "Z" is treated as UTC.
  TS_BSD=$(printf "%s" "$TS_NANO_STRIPPED" | sed -E 's/Z$/ +0000/')
  date -u -j -f "%Y-%m-%dT%H:%M:%S %z" "$TS_BSD" +%s 2>/dev/null || true
}

# Filter logs to only those whose timestamps fall within [start_epoch, end_epoch]
filter_logs_by_window() {
  LOG_INPUT="$1"
  START_EPOCH="$2"
  END_EPOCH="$3"
  FILTERED=""
  while IFS= read -r line; do
    # Extract leading ISO8601 timestamp. Example: 2025-01-01T00:00:00Z ...
    ts=$(printf "%s" "$line" | sed -nE 's/^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z).*/\1/p')
    if [ -n "$ts" ]; then
      epoch=$(to_epoch "$ts")
      if [ -n "$epoch" ] && [ "$epoch" -ge "$START_EPOCH" ] && [ "$epoch" -le "$END_EPOCH" ]; then
        FILTERED+="$line"$'\n'
      fi
    fi
  done <<< "$LOG_INPUT"
  printf "%s" "$FILTERED"
}

# Start the machine
flyctl machine start "$SCRAPER_MACHINE_ID" -a threads-scraper

# Smarter wait loop: poll until the machine is started (max 30 seconds)
MAX_WAIT=30
WAITED=0
while true; do
  STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
  if [[ "$STATUS" == "started" ]]; then
    echo "Machine $SCRAPER_MACHINE_ID is started."
    SCRAPE_START_EPOCH=$(date -u +%s)
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
# Define end of relevant log window relative to machine start
SCRAPE_END_EPOCH=$((SCRAPE_START_EPOCH + LOG_WINDOW_SECONDS))

# Run the command on the machine
echo "Running command: $CMD"
# Set environment variables in the command if they exist
ENV_CMD=""
if [[ -n "$SUPABASE_SERVICE_ROLE_KEY" ]]; then
  ENV_CMD="$ENV_CMD SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY"
fi
if [[ -n "$VITE_SUPABASE_URL" ]]; then
  ENV_CMD="$ENV_CMD VITE_SUPABASE_URL=$VITE_SUPABASE_URL"
fi
if [[ -n "$VITE_SUPABASE_ANON_KEY" ]]; then
  ENV_CMD="$ENV_CMD VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY"
fi

# Build a single command string to pass to flyctl (avoid multiple args)
if [[ -n "$ENV_CMD" ]]; then
  REMOTE_CMD="sh -lc 'cd /app && env $ENV_CMD $CMD'"
else
  REMOTE_CMD="sh -lc 'cd /app && $CMD'"
fi

# Execute the command in the machine
flyctl machine exec "$SCRAPER_MACHINE_ID" -a threads-scraper "$REMOTE_CMD"

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
       
       # Give Fly a moment to flush logs, then start polling
       echo "Waiting briefly for logs to propagate..."
       sleep 10
       
       # Check the logs for success/failure messages (most recent logs)
       echo "Checking machine logs for execution results..."
       
       # Poll for logs until we see the result (retry for up to ~1 min)
      LOGS=""
      for i in {1..12}; do
        echo "Attempt $i: Fetching logs..."
        # Fetch logs scoped to this machine. Older flyctl versions may not
        # support the --instance flag, so fall back to --machine if needed.
        LOGS=$(flyctl logs -a threads-scraper --instance "$SCRAPER_MACHINE_ID" --since 10m --no-tail 2>&1 || true)
        if echo "$LOGS" | grep -qi "unknown flag"; then
          echo "Instance flag unsupported, trying machine flag..."
          LOGS=$(flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 10m --no-tail 2>&1 || true)
        fi
        LOGS=$(echo "$LOGS" | tail -200)
        
        # Filter logs to the 2-minute window after machine start
        FILTERED_LOGS=$(filter_logs_by_window "$LOGS" "$SCRAPE_START_EPOCH" "$SCRAPE_END_EPOCH")
         
         # Debug: Show what we're getting
         echo "Filtered log length: ${#FILTERED_LOGS} characters"
         if [[ ${#FILTERED_LOGS} -gt 0 ]]; then
           # Show only a very short snippet to avoid overflowing GitHub logs
           echo "Last 25 chars of filtered logs: ${FILTERED_LOGS: -25}"
         fi
         
         # Check if we have the expected log messages (more flexible patterns)
         if echo "$FILTERED_LOGS" | grep -q "Method is working" || echo "$FILTERED_LOGS" | grep -q "Method stopped"; then
           echo "Found execution results in logs (attempt $i)"
           break
         else
           echo "No execution results found in logs (attempt $i), waiting 5 seconds..."
           sleep 5
         fi
       done
       
       echo "Relevant logs within ${LOG_WINDOW_SECONDS}s window after start (last 100 lines):"
       echo "$FILTERED_LOGS" | tail -100
       
       # Check for success message first (prioritize success) - more flexible patterns
       if echo "$FILTERED_LOGS" | grep -q "Method is working"; then
         echo "SUCCESS: Posts were successfully extracted"
         EXIT_CODE=0
       elif echo "$FILTERED_LOGS" | grep -q "Method stopped"; then
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
