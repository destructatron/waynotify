#!/bin/bash
# Complete integration test

set -e

echo "WayNotify Integration Test"
echo "==========================="
echo

# Clean up any existing processes
echo "Cleaning up old processes..."
pkill -f "waynotify" 2>/dev/null || true
sleep 1

# Start daemon in background
echo "Starting daemon..."
../src/waynotify &
DAEMON_PID=$!
echo "Daemon started (PID: $DAEMON_PID)"
sleep 2

# Verify daemon is running
if ! pgrep -f "waynotify" > /dev/null; then
    echo "ERROR: Daemon failed to start"
    exit 1
fi

# Check socket exists
SOCKET="$XDG_RUNTIME_DIR/waynotify/socket"
if [ ! -S "$SOCKET" ]; then
    echo "ERROR: Socket not found at $SOCKET"
    kill $DAEMON_PID 2>/dev/null || true
    exit 1
fi

echo "✓ Daemon running"
echo "✓ Socket exists: $SOCKET"
echo

# Test basic connection
echo "Testing connection..."
./test-simple.py
if [ $? -ne 0 ]; then
    echo "ERROR: Connection test failed"
    kill $DAEMON_PID 2>/dev/null || true
    exit 1
fi

echo "✓ Connection test passed"
echo

# Send test notifications
echo "Sending test notifications..."
notify-send "Test 1" "Normal notification"
notify-send -u critical "Test 2" "Critical notification"
notify-send -u low "Test 3" "Low priority notification"
notify-send "Test 4" "Notification with action" -A "default=Click Me"

echo "✓ Sent 4 test notifications"
echo

# Launch client
echo "Launching GTK client..."
echo "(Close the window to continue)"
../src/waynotify-client

# Clean up
echo
echo "Cleaning up..."
kill $DAEMON_PID 2>/dev/null || true
sleep 1

echo
echo "✓ All tests completed successfully!"
