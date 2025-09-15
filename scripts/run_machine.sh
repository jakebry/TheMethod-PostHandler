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
  echo "Machine is already running; stopping it to start fresh."
  flyctl machine stop "$SCRAPER_MACHINE_ID" -a "$APP" || true
  # wait until stopped
  for i in {1..20}; do
    STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
    [[ "$STATUS" == "stopped" ]] && break
    sleep 2
  done
fi

if [[ "$STATUS" == "stopped" ]] || [[ "$STATUS" == "suspended" ]]; then
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
  
  # Attach to logs immediately to avoid missing early lines
  LAUNCH_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  TMP_LOG=$(mktemp)
  echo "Starting live logs..."
  ( flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" | tee -a "$TMP_LOG" ) &
  LOGS_PID=$!

  echo "Waiting for machine to fully initialize..."
  sleep "$INIT_WAIT_SECONDS"

  # Best-effort: disable auto-stop during run to avoid flapping off mid-logs
  if flyctl machine update "$SCRAPER_MACHINE_ID" -a "$APP" --auto-stop=false >/dev/null 2>&1; then
    AUTO_STOP_DISABLED=true
  else
    AUTO_STOP_DISABLED=false
  fi
else
  echo "Machine $SCRAPER_MACHINE_ID is in unexpected state: $STATUS"
  echo "Checking machine logs for errors..."
  flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" --since 5m --no-tail | tail -50
  exit 1
fi
# Define end of relevant log window relative to machine start
SCRAPE_END_EPOCH=$((SCRAPE_START_EPOCH + LOG_WINDOW_SECONDS))

# Ensure we stop logs and the machine on exit
cleanup() {
  if [[ -n "$LOGS_PID" ]]; then
    kill "$LOGS_PID" 2>/dev/null || true
    wait "$LOGS_PID" 2>/dev/null || true
  fi
  if [[ -n "$TMP_LOG" && -f "$TMP_LOG" ]]; then
    rm -f "$TMP_LOG" || true
  fi
  # Re-enable auto-stop if we disabled it
  if [[ "$AUTO_STOP_DISABLED" == "true" ]]; then
    flyctl machine update "$SCRAPER_MACHINE_ID" -a "$APP" --auto-stop=true >/dev/null 2>&1 || true
  fi
  # Stop the machine (no --wait flag)
  flyctl machine stop "$SCRAPER_MACHINE_ID" -a "$APP" || true
  echo "Machine $SCRAPER_MACHINE_ID has been successfully stopped."
}
trap cleanup EXIT

# We don't exec any command; the machine's configured process will run on start.
# Record precise launch time so we can filter logs to this run only
LAUNCH_EPOCH=$(date -u +%s)
EXIT_CODE=0

# Wait for completion markers in logs (bounded)
if [[ $EXIT_CODE -eq 0 ]]; then
  COMPLETE=false
  SUCCESS=false
  WAIT_TIMEOUT_SECONDS=${WAIT_TIMEOUT_SECONDS:-1800} # 30 minutes
  SLEEP_INTERVAL=${SLEEP_INTERVAL:-5}
  WAITED=0
  KEPTALIVE=false
  echo "Waiting for completion markers in logs (timeout: ${WAIT_TIMEOUT_SECONDS}s)..."
  while [[ $WAITED -lt $WAIT_TIMEOUT_SECONDS ]]; do
    # Read the latest portion of the live log stream file
    SNAPSHOT=$(tail -n 4000 "$TMP_LOG" 2>/dev/null || true)
    
    # Narrow to only lines after the most recent boot or START marker
    START_LINE_NUM=$(printf "%s" "$SNAPSHOT" | nl -ba | grep -F "[START] Scraping threads and storing in Supabase" | tail -1 | awk '{print $1}' || true)
    if [[ -n "$START_LINE_NUM" ]]; then
      FILTERED=$(printf "%s" "$SNAPSHOT" | tail -n +$START_LINE_NUM)
    else
      # fallback: slice at the most recent boot marker if present
      BOOT_LINE_NUM=$(printf "%s" "$SNAPSHOT" | nl -ba | grep -F "Running Firecracker v" | tail -1 | awk '{print $1}' || true)
      if [[ -n "$BOOT_LINE_NUM" ]]; then
        FILTERED=$(printf "%s" "$SNAPSHOT" | tail -n +$BOOT_LINE_NUM)
      else
        FILTERED="$SNAPSHOT"
      fi
    fi
    
    # After we observe activity, attempt a best-effort keepalive to prevent auto-stop
    if [[ ( -n "$START_LINE_NUM" || -n "$BOOT_LINE_NUM" ) && "$KEPTALIVE" == "false" ]]; then
      if flyctl machine exec "$SCRAPER_MACHINE_ID" -a "$APP" "sh -lc 'nohup sleep 300 >/dev/null 2>&1 & echo KEPTALIVE'" >/dev/null 2>&1; then
        KEPTALIVE=true
      fi
    fi
    
    # Completion markers within this filtered window
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
    if printf "%s" "$FILTERED" | grep -q "Method is working - successfully extracted posts."; then
      COMPLETE=true
      SUCCESS=true
      break
    fi
    if printf "%s" "$FILTERED" | grep -q "\[DONE\] Scraping threads and storing in Supabase"; then
      COMPLETE=true
      SUCCESS=true
      break
    fi
    if printf "%s" "$FILTERED" | grep -q "machine exited with exit code 0, not restarting"; then
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
    # Stop live logs proactively before shutdown to avoid printing future runs
    if [[ -n "$LOGS_PID" ]]; then
      kill "$LOGS_PID" 2>/dev/null || true
      wait "$LOGS_PID" 2>/dev/null || true
      LOGS_PID=""
    fi
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
