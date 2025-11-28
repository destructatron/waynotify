# WayNotify Quick Start Guide

## Step 1: Install Dependencies

```bash
# Debian/Ubuntu
sudo apt install python3-gi python3-dasbus gir1.2-gtk-3.0 gir1.2-gtklayershell-0.1 gtk-layer-shell at-spi2-core

# Fedora
sudo dnf install python3-gobject python3-dasbus gtk3 gtk-layer-shell at-spi2-core

# Arch
sudo pacman -S python-gobject python-dasbus gtk3 gtk-layer-shell at-spi2-core
```

## Step 2: Install WayNotify

Copy the executables to `/usr/bin`:

```bash
sudo cp src/waynotify src/waynotify-client /usr/bin/
```

## Step 3: Disable Conflicting Notification Daemons

Kill any other notification daemon:

```bash
pkill xfce4-notifyd dunst mako notify-osd
```

## Step 4: Start the Daemon

```bash
waynotify
```

You can also add it to your compositor/window manager startup (e.g., Niri's `config.kdl`).

## Step 5: Launch the Client (Optional)

```bash
waynotify-client
```

## Step 5: Test

Send a test notification:

```bash
notify-send "Test" "Hello from WayNotify!"
```

Or run the test suite:

```bash
pytest
```

## Troubleshooting

### "Failed to acquire bus name" error

Another notification daemon is running. Run:
```bash
pkill xfce4-notifyd dunst mako  # Kill common daemons
./waynotify  # Try again
```

### Client won't connect

Make sure the daemon is running:
```bash
ps aux | grep waynotify
```

Check the socket exists:
```bash
ls -l $XDG_RUNTIME_DIR/waynotify/socket
```

### Orca not announcing

1. Make sure Orca is running: `orca`
2. Check AT-SPI2 is active: `ps aux | grep at-spi`
3. Launch the GTK client (not terminal): `./waynotify-client`

## Keyboard Shortcuts (in client)

- **Arrow Keys**: Navigate notifications
- **Enter**: Activate default action
- **Delete**: Dismiss notification
- **F5**: Refresh list
- **Escape**: Close client
- **Tab**: Move to action buttons

## Files

- `waynotify` - Notification daemon (D-Bus server)
- `waynotify-client` - GTK client application
