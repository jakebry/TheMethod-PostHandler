#!/usr/bin/env bash
# Test script to verify machine setup and basic functionality

set -e

APP=${FLY_APP:-threads-scraper}
MACHINE_ID=${SCRAPER_MACHINE_ID:?SCRAPER_MACHINE_ID env var is required}

echo "🧪 Testing Fly.io Machine Setup"
echo "================================"
echo "App: $APP"
echo "Machine ID: $MACHINE_ID"
echo ""

# Test 1: Check machine status
echo "1️⃣ Checking machine status..."
STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$MACHINE_ID\") | .state")
echo "Machine status: $STATUS"

if [[ "$STATUS" == "started" ]]; then
  echo "✅ Machine is already running"
elif [[ "$STATUS" == "stopped" ]] || [[ "$STATUS" == "suspended" ]]; then
  echo "🔄 Machine is suspended/stopped. Starting machine..."
  flyctl machine start "$MACHINE_ID" -a "$APP"
  
  # Wait for machine to start
  echo "Waiting for machine to start..."
  for i in {1..20}; do
    STATUS=$(flyctl machines list -a "$APP" --json | jq -r ".[] | select(.id==\"$MACHINE_ID\") | .state")
    if [[ "$STATUS" == "started" ]]; then
      echo "✅ Machine started successfully"
      break
    fi
    if [[ "$STATUS" == "failed" ]]; then
      echo "❌ Machine failed to start"
      exit 1
    fi
    echo "Status: $STATUS (attempt $i/20)"
    sleep 3
  done
else
  echo "❌ Machine is in unexpected state: $STATUS"
  exit 1
fi

# Test 2: Basic connectivity
echo ""
echo "2️⃣ Testing basic connectivity..."
if flyctl machine exec "$MACHINE_ID" -a "$APP" "echo 'Hello from machine!'"; then
  echo "✅ Basic connectivity works"
else
  echo "❌ Basic connectivity failed"
  exit 1
fi

# Test 3: Check Python environment
echo ""
echo "3️⃣ Testing Python environment..."
if flyctl machine exec "$MACHINE_ID" -a "$APP" "python --version"; then
  echo "✅ Python is available"
else
  echo "❌ Python is not available"
  exit 1
fi

# Test 4: Check if our script can be imported
echo ""
echo "4️⃣ Testing script imports..."
if flyctl machine exec "$MACHINE_ID" -a "$APP" "cd /app && python -c 'import src.main; print(\"✅ Script imports successfully\")'"; then
  echo "✅ Script imports work"
else
  echo "❌ Script import failed"
  echo "Checking for import errors..."
  flyctl machine exec "$MACHINE_ID" -a "$APP" "cd /app && python -c 'import src.main'" || true
  exit 1
fi

# Test 5: Check environment variables
echo ""
echo "5️⃣ Testing environment variables..."
flyctl machine exec "$MACHINE_ID" -a "$APP" "env | grep -E '(SUPABASE|PLAYWRIGHT)' || echo 'No environment variables found'"

echo ""
echo "🎉 All tests passed! Machine is ready for deployment."
echo ""
echo "To run the scraper:"
echo "  ./scripts/run_machine.sh"
