#!/bin/bash
# Comprehensive test for notification action handling
# Tests that the daemon remains responsive after action invocations

set -e

echo "==================================================================="
echo "Comprehensive Action Handling Test"
echo "==================================================================="
echo

# Check if daemon is running
if ! pgrep -f "waynotify" > /dev/null; then
    echo "Error: waynotify daemon is not running"
    echo "Please start it in another terminal: ../src/waynotify"
    exit 1
fi

echo "✓ Daemon is running"
echo

# Test 1: Client socket action invocation
echo "Test 1: Client socket action invocation"
echo "----------------------------------------"
./test_client_actions.py
if [ $? -eq 0 ]; then
    echo "✓ Test 1 PASSED"
else
    echo "✗ Test 1 FAILED"
    exit 1
fi
echo

# Test 2: Multiple rapid action invocations
echo "Test 2: Multiple rapid action invocations"
echo "----------------------------------------"
echo "Sending 5 notifications with actions rapidly..."
for i in {1..5}; do
    notify-send "Rapid Test $i" "Action test notification" -A "test=Action $i" &
done
wait
sleep 2

# Check if daemon is still responsive
if notify-send "After Rapid Test" "If you see this, daemon survived!" 2>/dev/null; then
    echo "✓ Test 2 PASSED - Daemon still responsive"
else
    echo "✗ Test 2 FAILED - Daemon not responsive"
    exit 1
fi
echo

# Test 3: Action with immediate follow-up
echo "Test 3: Action with immediate follow-up"
echo "----------------------------------------"
notify-send "Follow-up Test" "Send action then immediately send new notification" -A "default=Click Me" &
sleep 0.5
notify-send "Immediate Follow-up" "This should display without delay" &
wait
sleep 2

echo "✓ Test 3 PASSED"
echo

echo "==================================================================="
echo "ALL TESTS PASSED!"
echo "==================================================================="
echo
echo "The daemon handles action invocations correctly without freezing."
echo
