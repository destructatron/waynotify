# WayNotify

A lightweight, accessible notification daemon for Wayland compositors that implements the freedesktop.org D-Bus notification specification.

## Features

- **freedesktop.org compliant** - Full implementation of the org.freedesktop.Notifications D-Bus specification
- **GTK Layer Shell integration** - On-screen notification popups overlay on Wayland compositors
- **Full accessibility support** - AT-SPI2 integration for screen readers like Orca
- **Persistent notification history** - Review and interact with past notifications anytime
- **Action support** - Invoke notification actions even after popups expire
- **Do Not Disturb mode** - Suppress popups while still receiving notifications in history
- **Optional GTK client** - Browse notification history with full keyboard navigation and DND control

## Dependencies

### Required

- **Python 3.7+**
- **GTK 3** and GObject Introspection bindings for Python (`python-gobject` or `PyGObject`)
- **gtk-layer-shell** and its GObject Introspection library
- **at-spi2-core** - For accessibility support
- **dasbus** - Modern D-Bus library (Python package)

### Installation Examples

Debian/Ubuntu:
```bash
sudo apt install python3 python3-gi python3-dasbus gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 at-spi2-core
```

Fedora:
```bash
sudo dnf install python3 python3-gobject python3-dasbus gtk3 gtk-layer-shell at-spi2-core
```

Arch Linux:
```bash
sudo pacman -S python python-gobject python-dasbus gtk3 gtk-layer-shell at-spi2-core
```

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/destructatron/waynotify.git
   cd waynotify
   ```

2. **Install dependencies** (see above)

3. **Install executables:**
   ```bash
   sudo cp src/waynotify src/waynotify-client /usr/bin/
   ```

4. **Stop any conflicting notification daemons:**
   ```bash
   pkill dunst mako xfce4-notifyd notify-osd
   ```

5. **Add to your compositor config** (see below)

## Usage

### Starting WayNotify

Add WayNotify to your compositor's startup configuration:

#### Sway

Add to `~/.config/sway/config`:
```
exec waynotify
```

#### Hyprland

Add to `~/.config/hypr/hyprland.conf`:
```
exec-once = waynotify
```

#### River

Add to `~/.config/river/init`:
```bash
waynotify &
```

#### Niri

Add to `~/.config/niri/config.kdl`:
```kdl
spawn-at-startup "waynotify"
```

#### Other Compositors

Execute `waynotify` in your compositor's startup script or autostart configuration.

### Testing

After starting the daemon, test it with:
```bash
notify-send "Test" "Hello from WayNotify!"
notify-send -u critical "Urgent" "This is important!"
```

### Notification History Client (Optional)

WayNotify includes an optional GTK client for browsing notification history:

```bash
waynotify-client
```

Features include viewing past notifications, invoking actions, toggling Do Not Disturb mode, and full keyboard navigation (arrow keys, Enter, Delete, F5).

## Architecture

Applications send notifications to the WayNotify daemon via D-Bus using the freedesktop.org Notifications specification. The daemon displays them as GTK Layer Shell popups with AT-SPI2 accessibility and stores them in history. An optional GTK client can connect via Unix socket to browse notification history and control Do Not Disturb mode.

## Troubleshooting

### Daemon won't start

**Check for conflicting notification daemons:**
```bash
ps aux | grep -E 'dunst|mako|xfce4-notifyd|notify-osd'
pkill dunst mako xfce4-notifyd notify-osd
```

Only one notification daemon can own the `org.freedesktop.Notifications` D-Bus name at a time.

**Check logs:**
```bash
# Info log
cat /run/user/$(id -u)/waynotify/waynotify.log

# Error log
cat /run/user/$(id -u)/waynotify/error.log
```

**Verify D-Bus session:**
```bash
echo $DBUS_SESSION_BUS_ADDRESS
```

If empty, you may not be in a proper desktop session.

### No popups appear

- Ensure gtk-layer-shell is installed
- Check that your compositor supports Layer Shell protocol (most modern Wayland compositors do)
- Check error log for GTK or Layer Shell errors

### Client can't connect

- Verify the daemon is running: `ps aux | grep waynotify`
- Check socket exists: `ls -l /run/user/$(id -u)/waynotify/socket`

## D-Bus Interface

WayNotify implements the complete [freedesktop.org Notifications specification](https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html):

**Methods:**
- `GetServerInformation()` - Returns name, vendor, version, spec version
- `GetCapabilities()` - Returns supported capabilities
- `Notify()` - Display a notification
- `CloseNotification()` - Close a notification

**Signals:**
- `NotificationClosed` - Emitted when a notification is closed
- `ActionInvoked` - Emitted when a notification action is activated

**Capabilities:**
- `actions`, `body`, `body-markup`, `icon-static`, `persistence`, `sound`

## Configuration

WayNotify uses minimal configuration:

- **Socket location:** `$XDG_RUNTIME_DIR/waynotify/socket` (for client communication)
- **Logs:** `$XDG_RUNTIME_DIR/waynotify/waynotify.log` and `error.log`
- **D-Bus name:** `org.freedesktop.Notifications`

Popup appearance and behavior are currently hardcoded but can be modified in `src/waynotify`.

## Development

### Project Structure

```
waynotify/
├── src/
│   ├── waynotify         # Main daemon
│   └── waynotify-client  # GTK history client
├── tests/                # Test suite
└── docs/                 # Documentation
```

### Running Tests

```bash
# Install test dependencies
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install pytest pytest-asyncio pytest-timeout

# Run all tests
pytest

# Run specific categories
pytest -m unit           # Unit tests
pytest -m integration    # Integration tests
pytest -m dbus          # D-Bus compliance tests

# Run with coverage
pytest --cov=src --cov-report=html
```

See `tests/README.md` for detailed test documentation.

### Creating Custom Clients

The daemon exposes a Unix socket at `$XDG_RUNTIME_DIR/waynotify/socket` for custom clients. Messages are newline-terminated JSON objects.

**Supported message types:** `get_all`, `invoke_action`, `close`, `mark_read`, `get_dnd_state`, `set_dnd_state`

**Push notifications:** `new_notification`, `notification_closed`, `dnd_state_changed`

See `src/waynotify-client` for a full implementation example.

## Contributing

Contributions are welcome! Please ensure:
- Accessibility features are maintained
- Screen reader compatibility is tested with Orca
- D-Bus specification compliance is preserved
- Tests pass (`pytest`)

## License

MIT License - See LICENSE file for details.

## References

- [freedesktop.org Notification Specification](https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html)
- [GTK Layer Shell](https://github.com/wmww/gtk-layer-shell)
- [AT-SPI2 Documentation](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- [Orca Screen Reader](https://help.gnome.org/users/orca/stable/)
