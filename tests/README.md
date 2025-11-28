# WayNotify Test Suite

This directory contains the comprehensive test suite for WayNotify, organized as proper unit tests using pytest.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── test_connection.py       # Socket and daemon connection tests
├── test_dbus_spec.py        # D-Bus specification compliance tests
├── test_signals.py          # D-Bus signal emission tests
├── test_actions.py          # Notification action invocation tests
├── test_notifications.py    # Notification display and behavior tests
└── test_icons_markup.py     # Icon support and markup handling tests
```

## Running Tests

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run entire test suite
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests (no daemon required)
pytest -m unit

# Run only integration tests (require daemon)
pytest -m integration

# Run only D-Bus tests
pytest -m dbus

# Run only socket tests
pytest -m socket

# Exclude slow tests
pytest -m "not slow"
```

### Run Specific Test Files

```bash
# Test connection functionality
pytest tests/test_connection.py

# Test D-Bus spec compliance
pytest tests/test_dbus_spec.py

# Test signal emission
pytest tests/test_signals.py

# Test action invocation
pytest tests/test_actions.py

# Test notifications
pytest tests/test_notifications.py

# Test icons and markup
pytest tests/test_icons_markup.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/test_dbus_spec.py::TestServerInformation

# Run a specific test function
pytest tests/test_actions.py::TestActionInvocation::test_basic_action_invocation

# Run tests matching a pattern
pytest -k "action"
pytest -k "icon or markup"
```

## Test Markers

Tests are marked with the following pytest markers:

- `@pytest.mark.unit` - Unit tests (no daemon required)
- `@pytest.mark.integration` - Integration tests (require running daemon)
- `@pytest.mark.dbus` - Tests that use D-Bus
- `@pytest.mark.socket` - Tests that use Unix socket
- `@pytest.mark.slow` - Slow-running tests (can be excluded)

## Fixtures

Common fixtures available in `conftest.py`:

### Session-scoped Fixtures

- `daemon_process` - Starts waynotify daemon for testing
- `runtime_dir` - XDG_RUNTIME_DIR path
- `socket_path` - Unix socket path

### Function-scoped Fixtures

- `dbus_proxy` - D-Bus proxy for org.freedesktop.Notifications
- `socket_connection` - Connected socket (reader, writer)
- `socket_client` - SocketClient helper for requests
- `notification_signals` - Tracks NotificationClosed and ActionInvoked signals

## Test Coverage

The test suite covers:

1. **Connection Tests** (`test_connection.py`)
   - Daemon availability
   - Socket creation and connection
   - Request/response protocol
   - Multiple simultaneous connections

2. **D-Bus Specification** (`test_dbus_spec.py`)
   - GetServerInformation method
   - GetCapabilities method
   - Notify method (all parameters)
   - CloseNotification method
   - Parameter validation
   - Edge cases

3. **D-Bus Signals** (`test_signals.py`)
   - NotificationClosed signal
   - ActionInvoked signal
   - Signal parameters
   - Signal timing and ordering

4. **Action Invocation** (`test_actions.py`)
   - Basic action invocation
   - Multiple actions
   - Non-blocking behavior (critical!)
   - Delayed actions (after popup expires)
   - Request ID handling
   - Edge cases and errors

5. **Notifications** (`test_notifications.py`)
   - Basic notification creation
   - Urgency levels (low, normal, critical)
   - Timeouts (default, custom, persistent)
   - Notification replacement
   - Multiple notifications
   - History tracking

6. **Icons and Markup** (`test_icons_markup.py`)
   - Icon theme names
   - File paths and URIs
   - HTML markup support
   - HTML entities
   - Nested and malformed markup
   - Combining icons, markup, and actions

## Writing New Tests

### Basic Test Template

```python
import pytest

@pytest.mark.integration
@pytest.mark.dbus
class TestMyFeature:
    """Test description."""

    def test_something(self, daemon_process, dbus_proxy):
        """Test that something works."""
        # Arrange
        notif_id = dbus_proxy.Notify(...)

        # Act
        result = dbus_proxy.CloseNotification(notif_id)

        # Assert
        assert result is not None
```

### Async Test Template

```python
@pytest.mark.integration
@pytest.mark.socket
class TestAsyncFeature:
    """Test async operations."""

    async def test_async_operation(self, daemon_process, socket_client):
        """Test async functionality."""
        response = await socket_client.get_notifications()
        assert isinstance(response, list)
```

## Continuous Integration

The test suite is designed to run in CI environments:

```bash
# Quick checks (unit tests only)
pytest -m unit

# Full test suite (requires display and D-Bus)
pytest -m integration

# Exclude slow tests for faster CI
pytest -m "not slow"
```

## Debugging Failed Tests

### Increase Verbosity

```bash
pytest -vv                    # Very verbose
pytest --tb=long              # Long traceback format
pytest -s                     # Don't capture output (see prints)
```

### Run Single Test

```bash
pytest tests/test_actions.py::TestActionInvocation::test_basic_action_invocation -v
```

### Use pdb Debugger

```bash
pytest --pdb                  # Drop into pdb on failure
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb  # Use ipdb
```

### Check Daemon Logs

If tests fail, check the daemon logs:

```bash
cat /run/user/1000/waynotify/waynotify.log
cat /run/user/1000/waynotify/error.log
```

## Migration from Old Tests

The old test scripts have been converted to this pytest-based suite:

| Old Test Script | New Test Module | Status |
|----------------|-----------------|--------|
| test-simple.py | test_connection.py | ✓ Converted |
| test-client.sh | test_connection.py | ✓ Converted |
| test_spec_compliance.py | test_dbus_spec.py | ✓ Converted |
| test_signals.py | test_signals.py | ✓ Converted |
| test_markup.py | test_icons_markup.py | ✓ Converted |
| test_client_actions.py | test_actions.py | ✓ Converted |
| test_action_freeze.py | test_actions.py | ✓ Converted |
| test_action_id.py | test_actions.py | ✓ Converted |
| test_delayed_action.py | test_actions.py | ✓ Converted |
| test_notifications.sh | test_notifications.py | ✓ Converted |
| test_icon_support.sh | test_icons_markup.py | ✓ Converted |

Old test scripts can be archived or removed once the new suite is verified.

## Contributing

When adding new features to WayNotify:

1. Write tests first (TDD approach)
2. Use appropriate markers (@pytest.mark.integration, etc.)
3. Follow existing test structure and naming
4. Add docstrings explaining what's being tested
5. Run full test suite before submitting: `pytest -v`
