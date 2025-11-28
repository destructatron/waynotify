#!/bin/bash
# Complete test script

echo "WayNotify Test Suite"
echo "===================="
echo

# Check if daemon is running
if pgrep -f "waynotify" > /dev/null; then
    echo "✓ Daemon is running"
else
    echo "✗ Daemon not running"
    echo "  Starting daemon..."
    ../src/waynotify &
    DAEMON_PID=$!
    sleep 2

    if pgrep -f "waynotify" > /dev/null; then
        echo "✓ Daemon started (PID: $DAEMON_PID)"
    else
        echo "✗ Failed to start daemon"
        exit 1
    fi
fi

# Check socket
SOCKET="$XDG_RUNTIME_DIR/waynotify/socket"
if [ -S "$SOCKET" ]; then
    echo "✓ Socket exists: $SOCKET"
else
    echo "✗ Socket not found: $SOCKET"
    exit 1
fi

echo
echo "Testing basic connection..."
./test-simple.py
if [ $? -eq 0 ]; then
    echo "✓ Connection test passed"
else
    echo "✗ Connection test failed"
    exit 1
fi

echo
echo "Sending test notification..."
notify-send "WayNotify Test" "This is a test notification"
sleep 1

echo
echo "Launching GTK client..."
echo "(Close the window to continue)"
../src/waynotify-client

echo
echo "All tests completed!"
