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

# Check current machine status and start if needed
echo "Checking machine $SCRAPER_MACHINE_ID status..."
STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
echo "Current machine status: $STATUS"

if [[ "$STATUS" == "started" ]]; then
  echo "Machine $SCRAPER_MACHINE_ID is already running."
  SCRAPE_START_EPOCH=$(date -u +%s)
elif [[ "$STATUS" == "stopped" ]] || [[ "$STATUS" == "suspended" ]]; then
  echo "Starting machine $SCRAPER_MACHINE_ID..."
  flyctl machine start "$SCRAPER_MACHINE_ID" -a threads-scraper
  
  # Wait for machine to start (max 60 seconds)
  MAX_WAIT=60
  WAITED=0
  while true; do
    STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
    if [[ "$STATUS" == "started" ]]; then
      echo "Machine $SCRAPER_MACHINE_ID is started."
      SCRAPE_START_EPOCH=$(date -u +%s)
      break
    fi
    if [[ "$STATUS" == "failed" ]]; then
      echo "Machine $SCRAPER_MACHINE_ID failed to start. Status: $STATUS"
      echo "Checking machine logs for errors..."
      flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
      exit 1
    fi
    if (( WAITED >= MAX_WAIT )); then
      echo "Timed out waiting for machine $SCRAPER_MACHINE_ID to start."
      echo "Current status: $STATUS"
      echo "Checking machine logs for errors..."
      flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
      exit 1
    fi
    echo "Waiting for machine to start... (status: $STATUS, waited: ${WAITED}s)"
    sleep 3
    WAITED=$((WAITED+3))
  done
  
  echo "Waiting for machine to fully initialize..."
  sleep 10
else
  echo "Machine $SCRAPER_MACHINE_ID is in unexpected state: $STATUS"
  echo "Checking machine logs for errors..."
  flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
  exit 1
fi
# Define end of relevant log window relative to machine start
SCRAPE_END_EPOCH=$((SCRAPE_START_EPOCH + LOG_WINDOW_SECONDS))

# Run the command on the machine
echo "Running command: $CMD"
# Set environment variables in the command if they exist
ENV_CMD=""
if [[ -n "$SUPABASE_SERVICE_ROLE_KEY" ]]; then
  ENV_CMD="$ENV_CMD SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY"
fi
# App/runtime env
if [[ -n "$VITE_SUPABASE_URL" ]]; then
  ENV_CMD="$ENV_CMD VITE_SUPABASE_URL=$VITE_SUPABASE_URL"
fi
if [[ -n "$VITE_SUPABASE_ANON_KEY" ]]; then
  ENV_CMD="$ENV_CMD VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY"
fi
# Ensure Playwright uses appuser cache rather than root or mounted volume
ENV_CMD="$ENV_CMD HOME=/home/appuser XDG_CACHE_HOME=/home/appuser/.cache"

# Build a single command string to pass to flyctl (avoid multiple args)
if [[ -n "$ENV_CMD" ]]; then
  REMOTE_CMD="sh -lc 'cd /app && env $ENV_CMD $CMD'"
else
  REMOTE_CMD="sh -lc 'cd /app && $CMD'"
fi

# Verify machine is still running before executing command
STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
if [[ "$STATUS" != "started" ]]; then
  echo "Machine $SCRAPER_MACHINE_ID is not running (status: $STATUS). Cannot execute command."
  echo "Checking machine logs for errors..."
  flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
  exit 1
fi

# Execute the command in the machine
echo "Executing command on machine..."
if ! flyctl machine exec "$SCRAPER_MACHINE_ID" -a threads-scraper "$REMOTE_CMD"; then
  echo "Command execution failed. Checking machine status..."
  STATUS=$(flyctl machines list -a threads-scraper --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
  echo "Machine status after command failure: $STATUS"
  echo "Checking recent logs for errors..."
  flyctl logs -a threads-scraper --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
  EXIT_CODE=1
else
  echo "Command executed successfully."
  EXIT_CODE=0
fi

       # We already printed the exec output above; don't re-poll Fly logs.
       echo "No additional log polling needed; using exec output for result."

# Stop the machine (no --wait flag)
flyctl machine stop "$SCRAPER_MACHINE_ID" -a threads-scraper
echo "Machine $SCRAPER_MACHINE_ID has been successfully stopped."

# Exit with the appropriate code
exit $EXIT_CODE
