# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

WayNotify is an accessible notification daemon for Wayland/Linux that implements the freedesktop.org D-Bus notification specification. It displays on-screen notification popups using GTK Layer Shell with full AT-SPI2 accessibility support for screen readers like Orca.

**Architecture**: The daemon receives notifications via D-Bus, displays them as overlay popups on screen using GTK Layer Shell, and provides AT-SPI2 accessibility so screen readers like Orca announce them automatically. An optional GTK3 client provides notification history viewing and Do Not Disturb (DND) control.

## Development Commands

### Running the System

```bash
# Start the daemon (displays notifications on screen)
# If installed to /usr/bin:
waynotify

# Or run from source:
./src/waynotify

# OPTIONAL: Launch the GTK client for notification history (in another terminal)
waynotify-client  # or ./src/waynotify-client

# Test with notifications
notify-send "Test" "Hello World"
```

### Testing

WayNotify uses pytest for a comprehensive, organized test suite.

```bash
# Setup (one-time)
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install pytest pytest-asyncio pytest-timeout

# Run all tests
source venv/bin/activate  # Activate venv first
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest -m unit           # Unit tests (no daemon required)
pytest -m integration    # Integration tests (require daemon)
pytest -m dbus          # D-Bus tests
pytest -m socket        # Socket communication tests
pytest -m "not slow"    # Exclude slow tests

# Run specific test modules
pytest tests/test_connection.py      # Connection and socket tests
pytest tests/test_dbus_spec.py       # D-Bus spec compliance
pytest tests/test_signals.py         # D-Bus signal emission
pytest tests/test_actions.py         # Action invocation (critical!)
pytest tests/test_notifications.py   # Notification behavior
pytest tests/test_icons_markup.py    # Icons and HTML markup

# Run specific test
pytest tests/test_actions.py::TestActionNonBlocking::test_action_does_not_freeze_daemon

# Use the test runner script
./tests/run_tests.py --help         # See all options
./tests/run_tests.py --fast         # Quick test run
./tests/run_tests.py --coverage     # With coverage report

# Run with coverage
pytest --cov=src --cov-report=html
```

**Test Organization:**
- `test_connection.py` - Socket connections, daemon availability
- `test_dbus_spec.py` - freedesktop.org specification compliance
- `test_signals.py` - D-Bus signals (NotificationClosed, ActionInvoked)
- `test_actions.py` - Action invocation, non-blocking behavior
- `test_notifications.py` - Notification display, urgency, timeouts
- `test_icons_markup.py` - Icon support, HTML markup handling

See `tests/README.md` for detailed test documentation.

### Installation

```bash
# Install system dependencies
# Debian/Ubuntu:
sudo apt install python3-gi python3-dasbus gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 gtk-layer-shell at-spi2-core

# Install executables to /usr/bin
sudo cp src/waynotify src/waynotify-client /usr/bin/

# Disable conflicting notification daemons
pkill xfce4-notifyd dunst mako notify-osd
```

### Logging

WayNotify maintains two separate log files in `$XDG_RUNTIME_DIR/waynotify/`:

```bash
# Info log - notification details, connections, informational messages
cat /run/user/1000/waynotify/waynotify.log

# Error log - errors, exceptions, and stack traces only
cat /run/user/1000/waynotify/error.log
```

**Log file purposes:**
- `waynotify.log`: stdout is redirected here (print statements, notification details, client connections)
- `error.log`: stderr is redirected here (Python exceptions, tracebacks, error messages)

These logs are essential when running via D-Bus activation where terminal output is not visible.

## Architecture

### System Design

**waynotify** (notification server + display):
- Runs GTK/GLib main loop in main thread (required for GTK Layer Shell popups)
- Asyncio event loop integrated via `GLib.timeout_add(10, process_asyncio_events)`
- D-Bus service on `org.freedesktop.Notifications` (receives notifications from apps)
  - **Uses dasbus**: Modern D-Bus library with native asyncio support and non-blocking signals
- Unix socket server at `$XDG_RUNTIME_DIR/waynotify/socket` (optional, for history client)
- **On-screen popups**: Creates `NotificationPopup` GTK windows with Layer Shell positioning
- **AT-SPI2 accessibility**: Each popup has proper ATK role, name, and description for Orca

**waynotify-client** (optional history viewer):
- GTK3 application with asyncio event loop integrated via `GLib.timeout_add(10, process_asyncio_events)`
- Single `_message_reader()` coroutine reads from socket (critical: only ONE reader allowed)
- Request/response protocol: client adds `_request_id` to messages, daemon echoes it back
- Futures-based async API: responses matched by ID, push notifications go to callback

### Critical Event Loop Integration

**Daemon Event Loop** (NEW - GTK in main thread):
```python
# GTK must run in main thread for Layer Shell
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Process asyncio in GTK/GLib main loop
def process_asyncio_events():
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True
GLib.timeout_add(10, process_asyncio_events)

# D-Bus callbacks work seamlessly with asyncio (using dasbus)
if self.loop:
    asyncio.ensure_future(coro(), loop=self.loop)

# Start GTK main loop (blocks until quit)
Gtk.main()
```

**Client Event Loop**:
```python
# Create loop BEFORE GTK starts
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Process asyncio in GLib mainloop
def process_asyncio_events():
    loop.call_soon(loop.stop)
    loop.run_forever()
    return True  # Keep calling
GLib.timeout_add(10, process_asyncio_events)

# Schedule tasks with asyncio.ensure_future()
# NOT asyncio.run_coroutine_threadsafe() within same thread
```

**Client Window Creation**:
- Create placeholder window IMMEDIATELY in `do_activate()` or GTK exits
- Connect asynchronously in `GLib.idle_add()` callback after main loop starts
- Replace placeholder window once connected

### D-Bus with dasbus

**Simple, Non-Blocking Architecture**: Using **dasbus** instead of python-dbus provides native asyncio integration with non-blocking D-Bus operations.

**Service Definition**:
```python
from dasbus.connection import SessionMessageBus
from dasbus.server.interface import dbus_interface, dbus_signal

@dbus_interface("org.freedesktop.Notifications")
class NotificationDaemon:
    def __init__(self, loop=None):
        self.loop = loop  # Store asyncio loop reference
        # No ThreadPoolExecutor needed!

    # Methods use type hints instead of signature strings
    def GetServerInformation(self) -> Tuple[str, str, str, str]:
        return ('WayNotify', 'waynotify', '0.2', '1.2')

    @dbus_signal
    def NotificationClosed(self, notification_id: int, reason: int):
        pass
```

**Signal Emission** (non-blocking):
```python
# Direct calls work - dasbus signals are non-blocking
self.ActionInvoked(notification_id, action_key)
self.NotificationClosed(notification_id, reason)
```

**Service Publishing**:
```python
bus = SessionMessageBus()
daemon = NotificationDaemon(loop)
bus.publish_object(daemon.DBUS_PATH, daemon)
bus.register_service(daemon.DBUS_NAME)
```

**Variant Handling**: dasbus uses `Variant` objects that need unwrapping:
```python
def get_hint_value(hints: Dict, key: str, default=None):
    """Safely get a value from hints, unwrapping Variant if needed."""
    if key in hints and hasattr(hints[key], 'get_native'):
        return hints[key].get_native()
    return hints.get(key, default)
```

### Socket Protocol

**Message Format**: JSON lines (`\n` terminated)

**Request/Response Pattern**:
```python
# Client sends:
{"type": "get_all", "_request_id": 123}

# Daemon responds with same ID:
{"type": "notification_list", "_request_id": 123, "notifications": [...]}
```

**Supported Message Types**:
```python
# Notification management
{"type": "get_all", "_request_id": 123}
{"type": "invoke_action", "id": 1, "action": "default", "_request_id": 124}
{"type": "close", "id": 1, "_request_id": 125}
{"type": "mark_read", "id": 1, "_request_id": 126}

# Do Not Disturb control
{"type": "get_dnd_state", "_request_id": 127}
{"type": "set_dnd_state", "enabled": true, "_request_id": 128}
```

**Push Notifications** (no request_id):
```python
{"type": "new_notification", "notification": {...}}
{"type": "notification_closed", "id": 1}
{"type": "dnd_state_changed", "enabled": true}
```

**Single Reader Requirement**: Only `_message_reader()` coroutine reads from socket. It dispatches:
- Messages with `_request_id` → resolve pending Future
- Messages without → call update callback

### Notification Lifecycle and D-Bus Signals

**CRITICAL BEHAVIOR**: WayNotify uses a **delayed notification closure** pattern to support action invocation from the history client.

**Notification Lifecycle**:
1. **Notification received** → Stored in `self.notifications` dictionary
2. **Popup displayed** → On-screen popup shown with GTK Layer Shell
3. **Popup expires** (after timeout) → Popup dismissed **BUT notification kept in history**
4. **Action invoked** (from popup or client) → `ActionInvoked` + `NotificationClosed` signals emitted
5. **Explicit close** (via CloseNotification) → `NotificationClosed` signal emitted

**Key Design Decision - No NotificationClosed on Popup Expiration**:

When a notification popup expires (times out), WayNotify does **NOT** emit the `NotificationClosed` D-Bus signal. The notification remains in history for later action invocation via waynotify-client.

**Why this matters**:
- Applications like Discord listen for `ActionInvoked` signals to respond to user interactions
- If `NotificationClosed` is emitted when the popup expires, applications clean up their state and stop listening
- This breaks the workflow: user opens waynotify-client → clicks "Open Channel" → Discord doesn't respond
- By NOT emitting `NotificationClosed` on expiration, applications remain ready to handle actions

**When NotificationClosed IS emitted**:
1. **Action invoked** (reason 2 = Dismissed by user):
   ```python
   self.ActionInvoked(notification_id, action_key)
   self.NotificationClosed(notification_id, 2)
   ```
2. **Explicit CloseNotification call** (reason 3 = Closed by call):
   ```python
   self.NotificationClosed(notification_id, 3)
   ```

**Implementation** (src/waynotify:687-702):
```python
def _expire_notification(self, notification_id: int) -> bool:
    """
    Handle popup expiration timeout.

    NOTE: We do NOT emit NotificationClosed here because the notification is kept
    in history for later action invocation from the client. If we emit NotificationClosed,
    applications like Discord will clean up their state and stop listening for
    ActionInvoked signals, breaking the "click action in waynotify-client" workflow.
    """
    # Popup expired, but notification remains in history
    # Do not emit NotificationClosed - keep notification available for client actions
    return False
```

**Spec Deviation**: The freedesktop.org notification spec suggests emitting `NotificationClosed(reason=1, Expired)` when popups expire. WayNotify intentionally deviates from this to support persistent notification history with action invocation. This is critical for accessibility (users can review notifications at their own pace) and integration with applications that expect action signals after the popup disappears.

### Do Not Disturb (DND) Feature

**Purpose**: Allow users to suppress notification popups while still receiving and storing notifications in history.

**State Management**:
- DND state is stored in daemon (`self.dnd_enabled` boolean)
- State persists for the daemon's lifetime (resets on daemon restart)
- All connected clients sync automatically via broadcast messages

**Behavior When DND Enabled**:
- Notifications are received via D-Bus and saved to history
- `_announce_to_orca()` method checks DND state and skips popup creation
- No on-screen popups displayed
- No Orca announcements (since popups aren't shown)
- Notifications remain accessible via waynotify-client
- All notification data (actions, metadata) preserved

**Implementation** (src/waynotify:705-712):
```python
def _announce_to_orca(self, notification: Notification):
    """Show notification popup with AT-SPI2 accessibility for Orca"""
    try:
        # Skip showing popup if Do Not Disturb mode is enabled
        if self.dnd_enabled:
            print(f"DND mode: suppressing popup for notification {notification.id}")
            return
        # ... normal popup creation ...
```

**Client UI**:
- Toggle button in header bar labeled "DND"
- Button state syncs with daemon on client startup
- Clicking toggle sends `set_dnd_state` message to daemon
- All connected clients receive `dnd_state_changed` broadcast and update their toggle

**Socket Protocol** (see Socket Protocol section above):
- `get_dnd_state` - Query current DND state
- `set_dnd_state` - Enable/disable DND mode
- `dnd_state_changed` - Broadcast to all clients when state changes

**Use Cases**:
- Meetings/presentations - suppress popups without losing notifications
- Focus time - check notifications on your own schedule
- Accessibility - review notifications at your own pace via client

## Accessibility Implementation

### AT-SPI2 Integration

**Daemon Popups** (PRIMARY accessibility method):
- Each `NotificationPopup` window has `Atk.Role.NOTIFICATION`
- **No manual accessible_name/description**: Orca reads the natural GTK label text to prevent double announcements
- **HTML sanitization**: All HTML tags stripped from summary/body (prevents markup from being announced)
- GTK's native ATK framework automatically announces visible label text when popup appears
- Urgency hint set for critical notifications (`window.set_urgency_hint(True)`)
- **Standard GTK accessibility pattern**: Set role, let Orca traverse natural widget tree

**Client** (optional history viewer):
- Each `NotificationRow` has `Atk.Role.LIST_ITEM` (NOT `NOTIFICATION` - prevents auto-announcements)
- **No accessible_name/description**: Orca reads the natural GTK label text to prevent double announcements
- **Completely silent**: No announcements when opened or when new notifications arrive (daemon handles all announcements)
- **Navigation-only reading**: Orca only reads notifications when you navigate to them with arrow keys
- Full keyboard navigation: Arrow keys to browse, Enter to activate, Delete to dismiss
- Purpose: View notification history and interact with past notifications

### Screen Reader Testing

```bash
# Start Orca
orca

# Test announcement flow:
# 1. Start daemon: ./src/waynotify
# 2. Send notification: notify-send "Test" "Message"
# 3. Verify Orca announces the popup immediately
# 4. Test urgency: notify-send -u critical "Urgent" "Important message"

# OPTIONAL: Test history client (completely silent)
# 1. Launch client: ./src/waynotify-client
# 2. Verify NO announcements when client opens or updates
# 3. Use Up/Down arrows to navigate notification list
# 4. Verify Orca reads each notification ONLY when you navigate to it (not automatically)
# 5. Send a new notification and verify the client updates silently (no announcement)
```

## Common Issues and Solutions

### "Event loop is closed" Error
- **Cause**: Async tasks scheduled before event loop runs
- **Fix**: Show window immediately, schedule connection via `GLib.idle_add()`

### "Task was destroyed but it is pending"
- **Cause**: Tasks not properly cancelled before loop closes
- **Fix**: Cancel all tasks and await them in finally block

### "Multiple readers on socket" / "readuntil() called while another coroutine waiting"
- **Cause**: Multiple coroutines calling `reader.readline()`
- **Fix**: Single `_message_reader()` + request/response matching

### "Coroutine was never awaited" / "RuntimeError: no running event loop"
- **Cause**: `asyncio.create_task()` called from GLib callback (non-async context)
- **Fix**: Use `asyncio.ensure_future(coro, loop=loop)` instead (works with loop set via `set_event_loop()`)

### D-Bus "Failed to acquire bus name"
- **Cause**: Another notification daemon owns `org.freedesktop.Notifications`
- **Fix**: `pkill xfce4-notifyd dunst mako notify-osd notification-daemon`

### Orca Announces Notifications Twice
- **Cause**: Setting `accessible_name` and `accessible_description` on widgets AND having GTK labels with text
- **Fix**: Only set appropriate ATK role, remove `set_name()`/`set_description()` calls
- **Why**: Orca reads both the widget's accessible properties AND traverses child widgets, causing duplication
- **Solution**: Use GTK's natural accessibility - let Orca read the visible label text directly
- **Important role distinction**:
  - **Daemon popups**: Use `Atk.Role.NOTIFICATION` (triggers auto-announcement when popup appears)
  - **Client rows**: Use `Atk.Role.LIST_ITEM` (only announces when navigating, not automatically)

### Client Auto-Announces Notifications When Opening
- **Cause**: Using `Atk.Role.NOTIFICATION` on `NotificationRow` widgets in the client
- **Symptoms**: When opening waynotify-client or when notifications update, Orca automatically announces all notifications
- **Fix**: Use `Atk.Role.LIST_ITEM` instead of `Atk.Role.NOTIFICATION` for client rows
- **Why**: `NOTIFICATION` role tells screen readers to auto-announce (correct for daemon popups, wrong for client history viewer)
- **Solution**: Client should be completely silent except when navigating with arrow keys - the daemon handles all auto-announcements

### Variant Type Handling with dasbus

**Issue**: dasbus uses `Variant` objects for D-Bus variant types (`a{sv}` in hints, arrays, etc.)

**Symptoms**:
- Accessing `hints['urgency']` may return a Variant object instead of raw value
- JSON serialization fails with "Object of type Variant is not JSON serializable"

**Solution - Multiple Helper Functions**:

1. **`unwrap_variant(value)`** - Recursively unwraps Variant objects:
   ```python
   def unwrap_variant(value):
       """Recursively unwrap dasbus Variant objects to native Python values."""
       if hasattr(value, 'get_native'):
           value = value.get_native()
       # Recursively handle dicts, lists, tuples
       if isinstance(value, dict):
           return {k: unwrap_variant(v) for k, v in value.items()}
       elif isinstance(value, (list, tuple)):
           result = [unwrap_variant(item) for item in value]
           return tuple(result) if isinstance(value, tuple) else result
       return value
   ```

2. **`get_hint_value(hints, key, default)`** - Safe hint access:
   ```python
   urgency = get_hint_value(notification.hints, 'urgency', 1)
   ```

3. **`unwrap_hints_dict(hints)`** - Unwraps entire hints dictionary:
   ```python
   # In Notification.__init__:
   self.hints = unwrap_hints_dict(hints)  # Unwrap all values
   ```

4. **`ensure_json_serializable(obj)`** - Safety net for JSON serialization:
   ```python
   def ensure_json_serializable(obj):
       """Recursively ensure object is JSON serializable.
       Handles Variant, bytes, datetime, nested structures."""
       if hasattr(obj, 'get_native'):
           obj = obj.get_native()
           return ensure_json_serializable(obj)  # Recurse
       if isinstance(obj, dict):
           return {ensure_json_serializable(k): ensure_json_serializable(v)
                   for k, v in obj.items()}
       # ... handles all types ...
       return obj
   ```

**Critical Application Points**:
- **Notification creation**: Hints and actions unwrapped in `__init__`
- **Socket broadcasts**: `_broadcast_to_clients()` uses `ensure_json_serializable()`
- **Socket responses**: `handle_client()` uses `ensure_json_serializable()`

**Why This Matters**:
- Variant objects from D-Bus cannot be JSON serialized
- Must unwrap before sending to socket clients or storing
- Recursive unwrapping handles nested structures

**Test**: Run `./test_client_actions.py` to verify no JSON serialization errors

### notify-send "Unexpected reply type" Warning
- **Symptoms**: When using `notify-send`, you see "Unexpected reply type" printed to stderr
- **Impact**: Harmless - notifications work correctly, daemon functions properly
- **Cause**: Some versions of `notify-send` are overly strict about D-Bus type checking
- **Verification**: The daemon returns correct D-Bus type (`uint32`), confirmed via `dbus-send`
- **Workaround**: Use `notify-send 2>/dev/null` to suppress the warning

## Code Modification Guidelines

### When Modifying waynotify

1. **GTK runs in main thread**: All GTK operations (creating popups, etc.) can be called directly
2. **Async task scheduling**: Use `asyncio.ensure_future(coro, loop=self.loop)` to schedule async operations from sync contexts
3. **D-Bus with dasbus**:
   - Signal emission is non-blocking by default - just call `self.ActionInvoked()` or `self.NotificationClosed()`
   - No ThreadPoolExecutor needed
   - Use type hints on methods instead of signature strings
   - Hints parameter is `Dict[str, Variant]` - use `get_hint_value()` helper to unwrap values
4. **JSON serialization for socket clients**:
   - **ALWAYS** use `ensure_json_serializable()` before `json.dumps()` on data from D-Bus
   - Already applied in `_broadcast_to_clients()` and `handle_client()`
   - Prevents "Object of type Variant is not JSON serializable" errors
   - If adding new socket messages, wrap with `ensure_json_serializable(message)`
5. **Variant unwrapping**:
   - Notification.__init__ automatically unwraps hints and actions
   - Use `unwrap_variant()` for manual unwrapping
   - Use `get_hint_value()` for safe hint access
6. **Popup lifecycle**: Create with `NotificationPopup(notification)`, call `.show_all()`, popup handles own cleanup
7. **Accessibility required**: Set ATK role on widgets. DON'T set name/description on windows containing text labels (causes double reading in Orca)
8. **Client list thread safety**: Wrap in `with self.lock:`
9. **Socket cleanup**: Wrap writer.close() in try-except (connection may be closed)

### When Modifying waynotify-client

1. **Single socket reader rule**: Only `_message_reader()` reads from socket
2. **Request IDs required**: Add `_request_id` to outgoing messages
3. **Window creation**: Show window immediately in `do_activate()` to prevent exit
4. **Async task creation**: ALWAYS use `asyncio.ensure_future()`, NEVER `asyncio.create_task()` (GLib callbacks don't have running loop)
5. **Accessibility**:
   - Set `Atk.Role.LIST_ITEM` on notification rows (NOT `NOTIFICATION` - prevents auto-announcements)
   - DON'T set accessible_name/description (causes double reading in Orca)
   - Let Orca naturally read GTK widget labels when user navigates with arrow keys

### Testing Changes

```bash
# Manual testing for visual verification:

# Test notification display (daemon shows popups):
./src/waynotify
# In another terminal:
notify-send "Test" "Message"
# Popup should appear on screen in top-right corner

# Test with Orca (PRIMARY test):
orca &
./src/waynotify
notify-send "Test" "This should be announced by Orca"
# Orca should speak the notification immediately when popup appears

# Test urgency levels:
notify-send -u low "Low" "Low priority"
notify-send -u normal "Normal" "Normal priority"
notify-send -u critical "Critical" "Important message"

# OPTIONAL: Test history client (CRITICAL - must be completely silent):
./src/waynotify-client
# Should show notification history from daemon
# With Orca running:
# - Opening client should NOT announce any notifications
# - New notifications should update client silently
# - Only arrow key navigation should trigger Orca to read notifications

# Automated testing (ALWAYS run after code changes):
pytest -v                          # Run full test suite
pytest -m integration             # Integration tests only
pytest tests/test_actions.py      # Critical action tests
pytest -k "freeze"                # Test non-blocking behavior

# Quick verification:
pytest -m "not slow"              # Fast test subset

# With coverage:
pytest --cov=src --cov-report=html

# Test cleanup:
# Ctrl+C daemon - should close popups and exit cleanly
# No zombie processes or error messages
```

## Dependencies

**System**: `python3-gi gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 gtk-layer-shell at-spi2-core`
**Python**: `dasbus PyGObject` (see requirements.txt)

**Note**: GTK Layer Shell is required for on-screen notification popups on Wayland. Install via:
- Debian/Ubuntu: `sudo apt install gir1.2-gtklayershell-0.1`
- Arch: `sudo pacman -S gtk-layer-shell`
- Fedora: `sudo dnf install gtk-layer-shell`

**Note**: dasbus is required for D-Bus communication. Install via:
- `pip install dasbus>=1.6` OR
- System package if available (e.g., Orca 49 ships with dasbus)

## Project Structure

```
waynotify/
├── src/
│   ├── waynotify           # Main daemon (D-Bus + GTK Layer Shell + socket server)
│   └── waynotify-client    # Optional GTK3 history viewer
├── tests/                  # All test scripts
│   ├── test_*.py          # Python test scripts
│   ├── test_*.sh          # Shell test scripts
│   └── run-test.sh        # Comprehensive test suite
├── docs/                  # Documentation files
│   ├── COMPLIANCE.md      # freedesktop.org spec compliance
│   ├── TESTING.md         # Testing documentation
│   └── QUICK_START.md     # Quick start guide
├── CLAUDE.md             # This file - development guide for Claude Code
├── requirements.txt      # Python dependencies
├── README.md             # Main user documentation
└── LICENSE               # MIT License
```
