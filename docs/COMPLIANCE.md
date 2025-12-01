# Freedesktop.org Notification Specification Compliance

WayNotify implements the [freedesktop.org Desktop Notifications Specification version 1.2](https://specifications.freedesktop.org/notification-spec/1.2/).

## D-Bus Interface

- **Service Name:** `org.freedesktop.Notifications`
- **Object Path:** `/org/freedesktop/Notifications`
- **Interface:** `org.freedesktop.Notifications`

## Methods

### ✓ GetServerInformation
```
(STRING name, STRING vendor, STRING version, STRING spec_version) GetServerInformation()
```

**Returns:**
- `name`: "WayNotify"
- `vendor`: "waynotify"
- `version`: "0.2"
- `spec_version`: "1.2"

### ✓ GetCapabilities
```
as GetCapabilities()
```

**Returns array of capabilities:**
- `actions` - Action support
- `body` - Body text support
- `body-markup` - HTML markup support (preserved in storage, stripped for display/accessibility)
- `icon-static` - Static icon support (file paths, URIs, theme names, image data)
- `persistence` - Notification retention
- `sound` - Audio support via hints

### ✓ Notify
```
UINT32 Notify(STRING app_name, UINT32 replaces_id, STRING app_icon,
              STRING summary, STRING body, as actions, a{sv} hints, INT32 expire_timeout)
```

**Behavior:**
- Returns notification ID (always > 0)
- If `replaces_id` > 0 and exists, returns same ID (atomically replaces)
- If `replaces_id` > 0 but doesn't exist, creates new ID
- `expire_timeout` handling:
  - `-1`: Server default (5 seconds)
  - `0`: Never expires automatically
  - `> 0`: Expires after specified milliseconds

**Icon Support:**
- Icon theme names (e.g., "dialog-information")
- Absolute file paths (e.g., "/usr/share/pixmaps/icon.png")
- file:// URIs (e.g., "file:///path/to/icon.png")
- Image data from hints (`image-data`, `image_data`, `icon_data`)

**Markup Handling:**
- Original HTML markup preserved in notification storage
- Markup available to socket clients via `to_dict()`
- HTML stripped for display to prevent screen readers from announcing tags
- Complies with spec while maintaining accessibility

### ✓ CloseNotification
```
void CloseNotification(UINT32 id)
```

**Behavior:**
- Closes notification by ID
- Emits `NotificationClosed` signal with reason=3
- Handles non-existent IDs gracefully (no error)

## Signals

### ✓ NotificationClosed
```
NotificationClosed(UINT32 id, UINT32 reason)
```

**Reason codes:**
- `1` - Notification expired
- `2` - Dismissed by user (action button or close button)
- `3` - CloseNotification called
- `4` - Undefined/reserved

**Behavior:**
- Signal emitted AFTER notification removed from storage
- ID is invalidated before signal emission

### ✓ ActionInvoked
```
ActionInvoked(UINT32 id, STRING action_key)
```

**Behavior:**
- Emitted when user clicks action button in popup
- Works via popup button clicks and socket client requests
- Followed by `NotificationClosed` signal (reason=2)

### ⚠ ActivationToken
```
ActivationToken(UINT32 id, STRING activation_token)
```

**Status:** Not implemented
- This signal is optional per spec
- Used for X11 startup-id / Wayland xdg-activation
- Not critical for basic notification functionality

## Hints Support

The daemon properly handles standard hints including:

- `urgency` (byte) - 0=low, 1=normal, 2=critical
  - Critical notifications use red background and set urgency hint
- `sound-name` (string) - Plays system sound if specified
- `image-data` (struct) - Inline image data for icons
- `icon_data` (struct) - Legacy variant of image-data

All hint values are properly unwrapped from D-Bus Variants and made JSON-serializable for socket clients.

## Accessibility Compliance

While maintaining spec compliance for D-Bus clients:

- **Popup Display:** Shows plain text (HTML stripped) to prevent screen readers from announcing markup
- **AT-SPI2 Integration:** Each popup has `Atk.Role.NOTIFICATION` for automatic Orca announcements
- **Socket Clients:** Receive original HTML markup via JSON protocol
- **Best of Both Worlds:** Spec-compliant markup storage + accessible screen reader experience

## Testing

Comprehensive test suite validates specification compliance:

```bash
# Full specification compliance
./test_spec_compliance.py    # All D-Bus methods and parameters

# Signal behavior
./test_signals.py            # NotificationClosed and ActionInvoked signals

# Markup preservation
./test_markup.py             # body-markup capability

# Icon support
./test_icon_support.sh       # Theme names, file paths, URIs
```

## Deviations from Spec

**None.** WayNotify is fully compliant with the freedesktop.org Desktop Notifications Specification version 1.2.

The only optional feature not implemented is:
- `ActivationToken` signal (rarely used, for desktop activation tokens)

## Verification

All compliance tests pass:

```bash
✓ GetServerInformation returns correct spec version 1.2
✓ GetCapabilities returns required capabilities
✓ Notify returns valid ID > 0
✓ Notify correctly handles replaces_id
✓ Notify accepts actions, icons, hints, timeouts
✓ CloseNotification closes notifications
✓ CloseNotification handles invalid IDs gracefully
✓ NotificationClosed signal emitted with correct reasons
✓ ActionInvoked signal emitted for action buttons
✓ body-markup preserves HTML in storage
✓ Icon support for all formats (theme, file, URI, data)
```

## References

- [Desktop Notifications Specification 1.2](https://specifications.freedesktop.org/notification-spec/1.2/)
- [D-Bus Protocol Specification](https://specifications.freedesktop.org/notification-spec/1.2/protocol.html)
