"""
Pytest configuration and shared fixtures for WayNotify tests.
"""
import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest
from dasbus.connection import SessionMessageBus


# Add src directory to path for imports
SRC_DIR = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))


@pytest.fixture(scope="session")
def runtime_dir():
    """Get XDG_RUNTIME_DIR for socket paths."""
    return os.environ.get('XDG_RUNTIME_DIR', '/tmp')


@pytest.fixture(scope="session")
def socket_path(runtime_dir):
    """Get the Unix socket path for daemon communication."""
    return os.path.join(runtime_dir, 'waynotify', 'socket')


@pytest.fixture(scope="session")
def daemon_process():
    """
    Start the waynotify daemon for integration tests.

    Note: This assumes the daemon is not already running.
    The daemon will be terminated after all tests complete.
    """
    # Check if daemon is already running (exact match to avoid matching pgrep itself)
    try:
        result = subprocess.run(['pgrep', '-x', 'waynotify'],
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            pytest.skip("Daemon already running - using existing instance")
    except subprocess.CalledProcessError:
        pass

    # Start daemon
    daemon_path = SRC_DIR / "waynotify"
    if not daemon_path.exists():
        pytest.skip(f"Daemon not found at {daemon_path}")

    env = os.environ.copy()
    proc = subprocess.Popen(
        [str(daemon_path)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Wait for daemon to start (check for socket)
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    for _ in range(50):  # Wait up to 5 seconds
        if os.path.exists(socket_path):
            break
        time.sleep(0.1)
    else:
        proc.kill()
        pytest.fail("Daemon failed to start (socket not created)")

    yield proc

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def dbus_proxy():
    """Get D-Bus proxy for org.freedesktop.Notifications."""
    bus = SessionMessageBus()
    proxy = bus.get_proxy(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications"
    )
    return proxy


@pytest.fixture
async def socket_connection(socket_path):
    """
    Create a Unix socket connection to the daemon.

    Automatically connects and cleans up after the test.
    """
    if not os.path.exists(socket_path):
        pytest.skip(f"Socket not found at {socket_path}")

    reader, writer = await asyncio.open_unix_connection(socket_path)

    yield reader, writer

    # Cleanup
    try:
        writer.close()
        await writer.wait_closed()
    except Exception:
        pass


class SocketClient:
    """Helper class for socket-based daemon communication."""

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer
        self._next_request_id = 1

    async def send_request(self, request_type: str, timeout: float = 5.0, **kwargs):
        """
        Send a request to daemon and wait for response.

        Args:
            request_type: Type of request (e.g., 'get_all', 'invoke_action')
            timeout: Response timeout in seconds
            **kwargs: Additional request parameters

        Returns:
            Response dictionary from daemon

        Raises:
            asyncio.TimeoutError: If daemon doesn't respond in time
        """
        request_id = self._next_request_id
        self._next_request_id += 1

        request = {
            'type': request_type,
            '_request_id': request_id,
            **kwargs
        }

        self.writer.write((json.dumps(request) + '\n').encode())
        await self.writer.drain()

        # Read response with timeout
        response_data = await asyncio.wait_for(self.reader.readline(), timeout=timeout)
        return json.loads(response_data.decode().strip())

    async def get_notifications(self):
        """Get all notifications from daemon."""
        response = await self.send_request('get_all')
        if response.get('type') == 'notification_list':
            return response.get('notifications', [])
        return []

    async def invoke_action(self, notification_id: int, action: str):
        """Invoke an action on a notification."""
        response = await self.send_request(
            'invoke_action',
            id=notification_id,
            action=action
        )
        return response


@pytest.fixture
async def socket_client(socket_connection):
    """Get a SocketClient helper for tests."""
    reader, writer = socket_connection
    return SocketClient(reader, writer)


@pytest.fixture
def notification_signals():
    """
    Track D-Bus signals (NotificationClosed, ActionInvoked).

    Returns a dict with 'closed' and 'invoked' lists.
    """
    from gi.repository import GLib

    signals = {
        'closed': [],
        'invoked': []
    }

    bus = SessionMessageBus()
    proxy = bus.get_proxy(
        "org.freedesktop.Notifications",
        "/org/freedesktop/Notifications"
    )

    def on_closed(notif_id, reason):
        signals['closed'].append((notif_id, reason))

    def on_invoked(notif_id, action):
        signals['invoked'].append((notif_id, action))

    proxy.NotificationClosed.connect(on_closed)
    proxy.ActionInvoked.connect(on_invoked)

    return signals


# Mark all tests requiring daemon as integration tests by default
def pytest_collection_modifyitems(items):
    """Auto-mark tests based on their dependencies."""
    for item in items:
        # Mark tests using daemon_process fixture as integration
        if 'daemon_process' in item.fixturenames:
            item.add_marker(pytest.mark.integration)

        # Mark tests using dbus_proxy as dbus tests
        if 'dbus_proxy' in item.fixturenames:
            item.add_marker(pytest.mark.dbus)

        # Mark tests using socket fixtures
        if any(f in item.fixturenames for f in ['socket_connection', 'socket_client']):
            item.add_marker(pytest.mark.socket)
