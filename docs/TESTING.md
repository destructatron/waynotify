# Testing Guide

## Quick Test

The fastest way to test if everything works:

```bash
# Terminal 1: Start daemon
./waynotify

# Terminal 2: Launch client (should show window with no errors)
./waynotify-client

# Terminal 3: Send notification
notify-send "Test" "This should appear in the client"
```

## Expected Behavior

### Daemon Startup
```
Notification daemon started on D-Bus: org.freedesktop.Notifications
Client server listening on /run/user/1000/waynotify/socket
```

### Client Startup
1. Shows "Connecting to WayNotify daemon..." window with spinner
2. After ~0.1 seconds, shows main window with notification list
3. No error messages in terminal
4. Window stays open (doesn't exit immediately)

### When Notification Arrives
1. Appears in client list
2. Info bar shows announcement at top
3. Status bar updates count

## Automated Tests

### Basic Connection Test
```bash
./test-simple.py
```
Expected output:
```
Attempting to connect to: /run/user/1000/waynotify/socket
✓ Connected successfully!
✓ Retrieved 0 notifications
✓ Disconnected cleanly
```

### Full Integration Test
```bash
./test-full.sh
```
This will:
- Start daemon
- Verify socket
- Test connection
- Send 4 test notifications
- Launch client (you must close it to continue)
- Clean up

## Common Errors and Fixes

### "RuntimeError: no running event loop"
- **Status**: FIXED
- **Was**: Using `asyncio.create_task()` in non-async context
- **Fix**: Changed to `asyncio.ensure_future()`

### "Event loop is closed"
- **Status**: FIXED
- **Was**: Tasks scheduled before loop running
- **Fix**: Show window immediately, connect via `GLib.idle_add()`

### "Task was destroyed but it is pending"
- **Status**: FIXED
- **Was**: Tasks not cancelled before loop closes
- **Fix**: Proper cleanup in finally block

### Client exits immediately
- **Status**: FIXED
- **Was**: No window created in `do_activate()`
- **Fix**: Create placeholder window immediately

### "Request timeout"
- **Check**: Is daemon running? (`ps aux | grep waynotify`)
- **Check**: Does socket exist? (`ls $XDG_RUNTIME_DIR/waynotify/socket`)
- **Fix**: Start daemon first

### "Failed to acquire bus name"
- **Cause**: Another notification daemon running
- **Fix**: `./disable-other-notif-daemons.sh`

## Testing with Orca

```bash
# Start Orca first
orca &

# Start daemon
./waynotify &

# Launch client
./waynotify-client &

# Send notification
notify-send "Accessibility Test" "Orca should announce this"
```

Expected: Orca reads the info bar announcement when notification arrives.

## Manual Verification Checklist

- [ ] Daemon starts without errors
- [ ] Socket created at `$XDG_RUNTIME_DIR/waynotify/socket`
- [ ] Client shows connecting window
- [ ] Client shows main window after connection
- [ ] No tracebacks in terminal
- [ ] Sending notification makes it appear in client
- [ ] Info bar shows new notifications
- [ ] Arrow keys navigate notifications
- [ ] Enter key activates notification
- [ ] Delete key dismisses notification
- [ ] F5 refreshes list
- [ ] Client exits cleanly when closed
- [ ] Daemon continues running after client exit
- [ ] With Orca: notifications are announced

## Performance Testing

```bash
# Send many notifications quickly
for i in {1..50}; do
    notify-send "Test $i" "Message $i" &
done

# Client should handle all without freezing or crashing
```

## Debugging

### Enable verbose output
Edit waynotify or waynotify-client to add print statements.

### Check D-Bus
```bash
dbus-send --session --print-reply \
  --dest=org.freedesktop.Notifications \
  /org/freedesktop/Notifications \
  org.freedesktop.Notifications.GetServerInformation
```

Expected:
```
string "WayNotify"
string "waynotify"
string "0.1"
string "1.2"
```

### Monitor socket
```bash
# In one terminal
./waynotify

# In another, connect and send raw message
nc -U $XDG_RUNTIME_DIR/waynotify/socket
{"type": "get_all"}
# Should receive JSON response
```
