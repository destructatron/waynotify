"""
Tests for daemon connection and basic communication.

Tests socket connections, daemon availability, and basic request/response.
"""
import asyncio
import os
import subprocess

import pytest


class TestDaemonAvailability:
    """Test daemon process and socket availability."""

    @pytest.mark.integration
    def test_daemon_running(self, daemon_process):
        """Test that daemon process is running."""
        assert daemon_process.poll() is None, "Daemon process should be running"

    @pytest.mark.integration
    def test_socket_exists(self, daemon_process, socket_path):
        """Test that Unix socket is created."""
        assert os.path.exists(socket_path), f"Socket should exist at {socket_path}"
        assert os.path.stat(socket_path).st_mode & 0o140000, "Socket should be a socket file"


class TestSocketConnection:
    """Test Unix socket connection to daemon."""

    @pytest.mark.integration
    @pytest.mark.socket
    async def test_connect_to_socket(self, daemon_process, socket_connection):
        """Test basic socket connection."""
        reader, writer = socket_connection
        assert reader is not None, "Reader should be created"
        assert writer is not None, "Writer should be created"

    @pytest.mark.integration
    @pytest.mark.socket
    async def test_get_notifications(self, daemon_process, socket_client):
        """Test retrieving notification list from daemon."""
        notifications = await socket_client.get_notifications()
        assert isinstance(notifications, list), "Should return list of notifications"

    @pytest.mark.integration
    @pytest.mark.socket
    async def test_socket_request_response(self, daemon_process, socket_client):
        """Test request/response pattern with request IDs."""
        response = await socket_client.send_request('get_all')

        assert 'type' in response, "Response should have 'type' field"
        assert response['type'] == 'notification_list', "Should return notification_list"
        assert '_request_id' in response, "Response should echo request_id"

    @pytest.mark.integration
    @pytest.mark.socket
    @pytest.mark.timeout(10)
    async def test_socket_response_timeout(self, daemon_process, socket_client):
        """Test that invalid requests don't hang indefinitely."""
        # Even invalid requests should get some response or timeout
        try:
            response = await socket_client.send_request('invalid_request_type', timeout=2.0)
            # If we get a response, it should indicate an error
            assert response is not None
        except asyncio.TimeoutError:
            pytest.fail("Daemon should respond to invalid requests (even with error)")

    @pytest.mark.integration
    @pytest.mark.socket
    async def test_multiple_socket_connections(self, daemon_process, socket_path):
        """Test that daemon supports multiple simultaneous socket connections."""
        # Open multiple connections
        connections = []
        try:
            for _ in range(3):
                reader, writer = await asyncio.open_unix_connection(socket_path)
                connections.append((reader, writer))

            assert len(connections) == 3, "Should support multiple connections"

            # Each connection should work independently
            for reader, writer in connections:
                client = pytest.importorskip("conftest").SocketClient(reader, writer)
                notifications = await client.get_notifications()
                assert isinstance(notifications, list)

        finally:
            # Cleanup all connections
            for _, writer in connections:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass


class TestDaemonRequirements:
    """Tests that check for daemon requirements without starting it."""

    @pytest.mark.unit
    def test_daemon_executable_exists(self):
        """Test that daemon executable exists."""
        from pathlib import Path
        daemon_path = Path(__file__).parent.parent / "src" / "waynotify"
        assert daemon_path.exists(), f"Daemon should exist at {daemon_path}"
        assert os.access(daemon_path, os.X_OK), "Daemon should be executable"

    @pytest.mark.unit
    def test_client_executable_exists(self):
        """Test that client executable exists."""
        from pathlib import Path
        client_path = Path(__file__).parent.parent / "src" / "waynotify-client"
        assert client_path.exists(), f"Client should exist at {client_path}"
        assert os.access(client_path, os.X_OK), "Client should be executable"
