#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -e

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}
CMD=${1:-"python -m src.main"}
# Window (in seconds) after machine start to consider logs relevant for this run
LOG_WINDOW_SECONDS=${LOG_WINDOW_SECONDS:-120}

# Warm-up wait after a machine starts (seconds)
INIT_WAIT_SECONDS=${INIT_WAIT_SECONDS:-30}

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
STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
echo "Current machine status: $STATUS"

if [[ "$STATUS" == "started" ]]; then
  echo "Machine $SCRAPER_MACHINE_ID is already running."
  SCRAPE_START_EPOCH=$(date -u +%s)
elif [[ "$STATUS" == "stopped" ]] || [[ "$STATUS" == "suspended" ]]; then
  echo "Starting machine $SCRAPER_MACHINE_ID..."
  flyctl machine start "$SCRAPER_MACHINE_ID" -a "$APP"
  
  # Wait for machine to start (max 60 seconds)
  MAX_WAIT=60
  WAITED=0
  while true; do
    STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
    if [[ "$STATUS" == "started" ]]; then
      echo "Machine $SCRAPER_MACHINE_ID is started."
      SCRAPE_START_EPOCH=$(date -u +%s)
      break
    fi
    if [[ "$STATUS" == "failed" ]]; then
      echo "Machine $SCRAPER_MACHINE_ID failed to start. Status: $STATUS"
      echo "Start failure; refer to GitHub Actions exec output for logs."
      exit 1
    fi
    if (( WAITED >= MAX_WAIT )); then
      echo "Timed out waiting for machine $SCRAPER_MACHINE_ID to start."
      echo "Current status: $STATUS"
      echo "Timeout during start; refer to GitHub Actions exec output for logs."
      exit 1
    fi
    echo "Waiting for machine to start... (status: $STATUS, waited: ${WAITED}s)"
    sleep 3
    WAITED=$((WAITED+3))
  done
  
  echo "Waiting for machine to fully initialize..."
  sleep "$INIT_WAIT_SECONDS"
  # Start live logs early to keep the machine active and show output while we wait
  if [[ -z "$LOGS_PID" ]]; then
    echo "Starting live logs..."
    flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" &
    LOGS_PID=$!
  fi
else
  echo "Machine $SCRAPER_MACHINE_ID is in unexpected state: $STATUS"
  echo "Checking machine logs for errors..."
  flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
  exit 1
fi
# Define end of relevant log window relative to machine start
SCRAPE_END_EPOCH=$((SCRAPE_START_EPOCH + LOG_WINDOW_SECONDS))

# Proactively wait for exec readiness without changing exec timeouts
echo "Checking exec readiness..."
READY=false
READY_ATTEMPTS=0
MAX_READY_ATTEMPTS=${MAX_READY_ATTEMPTS:-40}
READY_SLEEP_SECONDS=${READY_SLEEP_SECONDS:-2}
while [[ $READY_ATTEMPTS -lt $MAX_READY_ATTEMPTS ]]; do
  if flyctl machine exec "$SCRAPER_MACHINE_ID" -a "$APP" "sh -lc 'echo ready'" >/dev/null 2>&1; then
    READY=true
    echo "Exec is ready."
    break
  fi
  READY_ATTEMPTS=$((READY_ATTEMPTS+1))
  echo "Waiting for exec readiness... attempt $READY_ATTEMPTS/$MAX_READY_ATTEMPTS"
  sleep "$READY_SLEEP_SECONDS"
done

if [[ "$READY" != "true" ]]; then
  echo "Machine did not report exec-ready in time. Proceeding to background launch attempts anyway."
fi

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
ENV_CMD="$ENV_CMD HOME=/home/appuser XDG_CACHE_HOME=/home/appuser/.cache METHOD_HISTORY_DIR=/app/.cache/method_history"

# Build a single command string to pass to flyctl (avoid multiple args)
if [[ -n "$ENV_CMD" ]]; then
  REMOTE_CMD="sh -lc 'cd /app && env $ENV_CMD $CMD'"
else
  REMOTE_CMD="sh -lc 'cd /app && $CMD'"
fi

# For reliability in CI, run the scraper in the background and stream logs until it finishes.
# Tag this run with a unique RUN_ID so we can filter logs precisely.
RUN_ID="RUN_$(date -u +%Y%m%dT%H%M%SZ)_$RANDOM"
# Run in background subshell without nohup; stream to init stdout
REMOTE_CMD_BG="sh -lc 'cd /app && echo $RUN_ID:START && ( $CMD; EC=$?; echo $RUN_ID:EXIT:$EC ) >/proc/1/fd/1 2>&1 & echo BACKGROUND_STARTED'"

# Verify machine is still running before executing command
STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
if [[ "$STATUS" != "started" ]]; then
  echo "Machine $SCRAPER_MACHINE_ID is not running (status: $STATUS). Cannot execute command."
  echo "Not executing; refer to GitHub Actions exec output for logs."
  exit 1
fi

# Ensure we stop logs and the machine on exit
cleanup() {
  if [[ -n "$LOGS_PID" ]]; then
    kill "$LOGS_PID" 2>/dev/null || true
    wait "$LOGS_PID" 2>/dev/null || true
  fi
  # Stop the machine (no --wait flag)
  flyctl machine stop "$SCRAPER_MACHINE_ID" -a "$APP" || true
  echo "Machine $SCRAPER_MACHINE_ID has been successfully stopped."
}
trap cleanup EXIT

echo "Launching scraper in background via exec..."
# Record precise launch time so we can filter logs to this run only
LAUNCH_EPOCH=$(date -u +%s)

# Retry background launch a few times, re-checking machine status and exec readiness
MAX_LAUNCH_RETRIES=${MAX_LAUNCH_RETRIES:-8}
LAUNCH_SLEEP=${LAUNCH_SLEEP:-5}
ATTEMPT=1
BG_STARTED=false
while [[ $ATTEMPT -le $MAX_LAUNCH_RETRIES ]]; do
  echo "Launch attempt $ATTEMPT/$MAX_LAUNCH_RETRIES..."
  STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
  if [[ "$STATUS" != "started" ]]; then
    echo "Machine not in started state (status: $STATUS). Starting..."
    flyctl machine start "$SCRAPER_MACHINE_ID" -a "$APP" || true
    sleep "$LAUNCH_SLEEP"
  fi
  # Re-check lightweight exec readiness
  if flyctl machine exec "$SCRAPER_MACHINE_ID" -a "$APP" "sh -lc 'echo ready'" >/dev/null 2>&1; then
    if flyctl machine exec "$SCRAPER_MACHINE_ID" -a "$APP" "$REMOTE_CMD_BG" | grep -q "BACKGROUND_STARTED"; then
      BG_STARTED=true
      break
    fi
  fi
  echo "Launch attempt $ATTEMPT failed; retrying shortly..."
  sleep "$LAUNCH_SLEEP"
  ATTEMPT=$((ATTEMPT+1))
done

if [[ "$BG_STARTED" == "true" ]]; then
  echo "Background process started; streaming logs until completion..."
  # Start live logs after launch to avoid replaying earlier runs
  echo "Starting live logs..."
  flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" &
  LOGS_PID=$!
  EXIT_CODE=0
else
  echo "Failed to launch background process after $MAX_LAUNCH_RETRIES attempts."
  EXIT_CODE=1
fi

# If background launch succeeded, wait for completion markers in logs (bounded)
if [[ $EXIT_CODE -eq 0 ]]; then
  COMPLETE=false
  SUCCESS=false
  WAIT_TIMEOUT_SECONDS=${WAIT_TIMEOUT_SECONDS:-1800} # 30 minutes
  SLEEP_INTERVAL=${SLEEP_INTERVAL:-5}
  WAITED=0
  echo "Waiting for completion markers in logs (timeout: ${WAIT_TIMEOUT_SECONDS}s)..."
  while [[ $WAITED -lt $WAIT_TIMEOUT_SECONDS ]]; do
    # Fetch recent logs snapshot and filter to this run window
    SNAPSHOT=$(flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" --no-tail 2>/dev/null | tail -800 || true)
    NOW_EPOCH=$(date -u +%s)
    FILTERED=$(filter_logs_by_window "$SNAPSHOT" "$LAUNCH_EPOCH" "$NOW_EPOCH")
    # Look for our explicit RUN_ID exit marker first
    if printf "%s" "$FILTERED" | grep -q "$RUN_ID:EXIT:"; then
      COMPLETE=true
      EXIT_LINE=$(printf "%s" "$FILTERED" | grep "$RUN_ID:EXIT:" | tail -1)
      EXIT_CODE=$(printf "%s" "$EXIT_LINE" | awk -F: '{print $3}')
      if [[ "$EXIT_CODE" == "0" ]]; then
        SUCCESS=true
      else
        SUCCESS=false
      fi
      break
    fi
    # Fallback markers (same-run only)
    if printf "%s" "$FILTERED" | grep -q "\[END\] Scraper finished"; then
      COMPLETE=true
      SUCCESS=true
      break
    fi
    if printf "%s" "$FILTERED" | grep -q "Scraping process completed."; then
      COMPLETE=true
      SUCCESS=true
      break
    fi
    if printf "%s" "$FILTERED" | grep -q "Main child exited normally with code: 0"; then
      COMPLETE=true
      SUCCESS=true
      break
    fi
    if printf "%s" "$FILTERED" | grep -Ei "error|traceback|exception" >/dev/null; then
      # Heuristic: error seen
      COMPLETE=true
      SUCCESS=false
      break
    fi
    sleep "$SLEEP_INTERVAL"
    WAITED=$((WAITED+SLEEP_INTERVAL))
  done

  if [[ "$COMPLETE" == "true" ]]; then
    if [[ "$SUCCESS" == "true" ]]; then
      echo "Detected successful completion in logs."
      EXIT_CODE=0
    else
      echo "Detected error completion in logs."
      EXIT_CODE=1
    fi
  else
    echo "Timed out waiting for completion markers."
    EXIT_CODE=1
  fi
fi

# Exit with the appropriate code (trap will stop machine)
exit $EXIT_CODE
