#!/usr/bin/env bash
# Start an existing Fly.io machine, run a command, then stop the machine.
# Requires FLY_API_TOKEN for authentication and SCRAPER_MACHINE_ID set to the Machine ID.

set -e

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}

# Warm-up wait after a machine starts (seconds)
INIT_WAIT_SECONDS=${INIT_WAIT_SECONDS:-30}

# Check current machine status and start if needed
echo "Checking machine $SCRAPER_MACHINE_ID status..."
STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
echo "Current machine status: $STATUS"

if [[ "$STATUS" == "started" ]]; then
  echo "Machine $SCRAPER_MACHINE_ID is already running; stopping for a clean start."
  flyctl machine stop "$SCRAPER_MACHINE_ID" -a "$APP" || true
  MAX_WAIT=60
  WAITED=0
  while true; do
    STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$SCRAPER_MACHINE_ID\") | .state")
    if [[ "$STATUS" == "stopped" || "$STATUS" == "suspended" ]]; then
      echo "Machine $SCRAPER_MACHINE_ID stopped."
      break
    fi
    if (( WAITED >= MAX_WAIT )); then
      echo "Timed out waiting for machine $SCRAPER_MACHINE_ID to stop."
      exit 1
    fi
    echo "Waiting for machine to stop... (status: $STATUS, waited: ${WAITED}s)"
    sleep 3
    WAITED=$((WAITED+3))
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
  
    echo "Waiting for machine to fully initialize..."
    sleep "$INIT_WAIT_SECONDS"
    # Record launch timestamp and start live logs streaming to a file and stdout
    LAUNCH_ISO=$(date -u -d "@$(($SCRAPE_START_EPOCH-5))" +%Y-%m-%dT%H:%M:%SZ)
    TMP_LOG=$(mktemp)
    echo "Starting live logs..."
    (
      flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" \
      | awk -v launch="$LAUNCH_ISO" '
          function stripFrac(s){ sub(/\.[0-9]+Z$/, "Z", s); return s }
          BEGIN{seen_time=0; started=0}
          {
            if (match($0, /^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z)/, a)) {
              ts = stripFrac(a[1]);
              if (ts >= launch) { seen_time=1 }
            }
            if (seen_time && index($0, "[START] Scraping threads and storing in Supabase")>0) { started=1 }
            if (started) { print; fflush() }
          }
        ' | tee -a "$TMP_LOG"
    ) &
    LOGS_PID=$!
  # Best-effort: disable auto-stop during run to avoid flapping off mid-logs
  if flyctl machine update "$SCRAPER_MACHINE_ID" -a "$APP" --auto-stop=false >/dev/null 2>&1; then
    AUTO_STOP_DISABLED=true
  else
    AUTO_STOP_DISABLED=false
  fi
else
  echo "Machine $SCRAPER_MACHINE_ID is in unexpected state: $STATUS"
  echo "Checking machine logs for errors..."
  flyctl logs -a "$APP" --machine "$SCRAPER_MACHINE_ID" --no-tail | tail -50
  exit 1
fi
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
EXIT_CODE=0

# If background launch succeeded, wait for completion markers in logs (bounded)
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
    
    # Narrow to only lines after the most recent [START] marker in this snapshot
    START_LINE_NUM=$(printf "%s" "$SNAPSHOT" | nl -ba | grep -F "[START] Scraping threads and storing in Supabase" | tail -1 | awk '{print $1}' || true)
    if [[ -n "$START_LINE_NUM" ]]; then
      FILTERED=$(printf "%s" "$SNAPSHOT" | tail -n +$START_LINE_NUM)
    else
      FILTERED="$SNAPSHOT"
    fi
    
    # After we observe a START for this run, attempt a best-effort keepalive to prevent auto-stop
    if [[ -n "$START_LINE_NUM" && "$KEPTALIVE" == "false" ]]; then
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
