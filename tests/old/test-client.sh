#!/bin/bash
# Simple test to check if client connects

echo "Testing WayNotify client connection..."
echo

# Check if daemon is running
if ! pgrep -f "waynotify" > /dev/null; then
    echo "ERROR: Daemon not running"
    echo "Start with: ../src/waynotify"
    exit 1
fi

# Check socket exists
SOCKET="$XDG_RUNTIME_DIR/waynotify/socket"
if [ ! -S "$SOCKET" ]; then
    echo "ERROR: Socket not found at $SOCKET"
    exit 1
fi

echo "Daemon is running ✓"
echo "Socket exists ✓"
echo
echo "Launching client..."
../src/waynotify-client
