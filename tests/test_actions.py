"""
Tests for notification actions.

Tests action invocation from socket (client), non-blocking behavior,
and proper signal emission. Consolidates tests from:
- test_client_actions.py
- test_action_freeze.py
- test_action_id.py
- test_delayed_action.py
"""
import asyncio
import time

import pytest


@pytest.mark.integration
@pytest.mark.socket
class TestActionInvocation:
    """Test action invocation via socket."""

    async def test_basic_action_invocation(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test basic action invocation through socket."""
        # Create notification with actions
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Action Test",
            "Testing basic action",
            ["action1", "First Action"],
            {},
            30000
        )

        await asyncio.sleep(0.5)

        # Invoke action
        response = await socket_client.invoke_action(notif_id, "action1")

        assert response is not None, "Should receive response"
        assert response.get('type') == 'action_result', "Should return action_result"
        assert response.get('success'), "Action should succeed"

    async def test_action_with_multiple_choices(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test notification with multiple action choices."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Multiple Actions",
            "Choose one",
            ["action1", "Option 1", "action2", "Option 2", "action3", "Option 3"],
            {}, 30000
        )

        await asyncio.sleep(0.5)

        # Invoke second action
        response = await socket_client.invoke_action(notif_id, "action2")

        assert response.get('success'), "Should invoke specific action"

    async def test_default_action(self, daemon_process, dbus_proxy, socket_client):
        """Test default action invocation."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Default Action",
            "Has default action",
            ["default", "Default Action"],
            {}, 30000
        )

        await asyncio.sleep(0.5)

        response = await socket_client.invoke_action(notif_id, "default")

        assert response.get('success'), "Should invoke default action"


@pytest.mark.integration
@pytest.mark.socket
class TestActionNonBlocking:
    """Test that action invocation doesn't freeze the daemon."""

    @pytest.mark.timeout(10)
    async def test_action_does_not_freeze_daemon(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """
        Test that invoking an action doesn't freeze the daemon.

        This is critical: the daemon should remain responsive after action invocation.
        """
        # Create notification with actions
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Freeze Test",
            "Testing non-blocking action",
            ["action1", "Click Me"],
            {}, 30000
        )

        await asyncio.sleep(0.5)

        # Invoke action
        response = await socket_client.invoke_action(notif_id, "action1")

        assert response.get('success'), "Action should succeed"

        # Test daemon responsiveness - should respond quickly
        try:
            info = await asyncio.wait_for(
                asyncio.to_thread(dbus_proxy.GetServerInformation),
                timeout=5.0
            )
            assert info is not None, "Daemon should respond after action"
        except asyncio.TimeoutError:
            pytest.fail("Daemon froze after action invocation!")

    @pytest.mark.timeout(15)
    async def test_multiple_sequential_actions(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that multiple actions can be invoked without freezing."""
        notif_ids = []

        # Create multiple notifications with actions
        for i in range(3):
            notif_id = dbus_proxy.Notify(
                "test-app", 0, "", f"Action {i}",
                f"Notification {i}",
                ["action1", "Action 1", "action2", "Action 2"],
                {}, 30000
            )
            notif_ids.append(notif_id)

        await asyncio.sleep(0.5)

        # Invoke actions on each
        for notif_id in notif_ids:
            response = await socket_client.invoke_action(notif_id, "action1")
            assert response.get('success'), f"Action on {notif_id} should succeed"

            # Verify daemon still responsive
            info = await asyncio.to_thread(dbus_proxy.GetServerInformation)
            assert info is not None, "Daemon should remain responsive"

    @pytest.mark.timeout(10)
    async def test_notification_after_action(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that new notifications work after action invocation."""
        # Create and invoke action
        notif_id1 = dbus_proxy.Notify(
            "test-app", 0, "", "First", "First notification",
            ["action1", "Click"], {}, 30000
        )

        await asyncio.sleep(0.5)
        await socket_client.invoke_action(notif_id1, "action1")

        # Create new notification - should work
        notif_id2 = dbus_proxy.Notify(
            "test-app", 0, "", "Second",
            "Second notification after action", [], {}, 5000
        )

        assert notif_id2 > 0, "Should create notification after action invocation"
        assert notif_id2 != notif_id1, "Should be a new notification"


@pytest.mark.integration
@pytest.mark.socket
class TestActionEdgeCases:
    """Test edge cases and error conditions for actions."""

    async def test_action_on_nonexistent_notification(
        self, daemon_process, socket_client
    ):
        """Test invoking action on non-existent notification."""
        response = await socket_client.invoke_action(99999, "action1")

        # Should handle gracefully
        assert response is not None, "Should receive response"
        # Implementation may return success=false or error
        if 'success' in response:
            assert not response['success'], "Should indicate failure for non-existent ID"

    async def test_action_with_invalid_action_key(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test invoking non-existent action key."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Test", "Has actions",
            ["action1", "Valid Action"], {}, 30000
        )

        await asyncio.sleep(0.5)

        # Try to invoke action that doesn't exist
        response = await socket_client.invoke_action(notif_id, "nonexistent_action")

        assert response is not None, "Should receive response"
        # Should indicate failure for invalid action
        if 'success' in response:
            assert not response['success'], "Should fail for invalid action key"

    async def test_action_on_notification_without_actions(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test invoking action on notification that has no actions."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "No Actions",
            "This notification has no actions", [], {}, 30000
        )

        await asyncio.sleep(0.5)

        response = await socket_client.invoke_action(notif_id, "action1")

        assert response is not None, "Should receive response"
        # Should handle gracefully
        if 'success' in response:
            assert not response['success'], "Should fail - no actions available"

    async def test_action_with_zero_id(self, daemon_process, socket_client):
        """Test action invocation with ID 0."""
        # ID 0 is special (means "don't replace")
        response = await socket_client.invoke_action(0, "action1")

        assert response is not None, "Should handle ID 0 gracefully"


@pytest.mark.integration
@pytest.mark.socket
@pytest.mark.slow
class TestDelayedActions:
    """Test actions invoked after popup expires (from history)."""

    async def test_action_after_popup_expires(
        self, daemon_process, dbus_proxy, socket_client, notification_signals
    ):
        """
        Test that actions can be invoked after popup expires.

        This is critical for the history viewer - users should be able
        to click actions in waynotify-client even after popup is gone.
        """
        # Create notification with short timeout
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Delayed Action Test",
            "Will expire quickly",
            ["action1", "Click Later"],
            {}, 1000  # 1 second timeout
        )

        # Wait for popup to expire
        await asyncio.sleep(2.0)

        notification_signals['invoked'].clear()
        notification_signals['closed'].clear()

        # Now invoke action (simulates clicking in history client)
        response = await socket_client.invoke_action(notif_id, "action1")

        assert response.get('success'), "Should be able to invoke action after expiration"

        # Signal should still be emitted
        await asyncio.sleep(0.5)
        assert len(notification_signals['invoked']) > 0, \
            "ActionInvoked signal should be emitted for delayed action"

    async def test_notification_remains_in_history_after_expiration(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that expired notifications remain in history."""
        # Create notification with short timeout
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "History Test",
            "Should remain in history",
            ["action1", "Action"], {}, 1000
        )

        # Wait for expiration
        await asyncio.sleep(2.0)

        # Get notifications from daemon
        notifications = await socket_client.get_notifications()

        # Find our notification
        matching = [n for n in notifications if n.get('id') == notif_id]
        assert len(matching) > 0, \
            "Expired notification should remain in history for action invocation"


@pytest.mark.integration
@pytest.mark.socket
class TestRequestIdHandling:
    """Test request ID handling in action invocation."""

    async def test_request_id_echoed_in_response(
        self, daemon_process, socket_connection, dbus_proxy
    ):
        """Test that daemon echoes request_id in action responses."""
        reader, writer = socket_connection

        # Create notification
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Request ID Test",
            "Testing request IDs",
            ["action1", "Action"], {}, 30000
        )

        await asyncio.sleep(0.5)

        # Send action request with specific request_id
        import json
        request = {
            'type': 'invoke_action',
            'id': notif_id,
            'action': 'action1',
            '_request_id': 42
        }

        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        # Read response
        response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(response_data.decode().strip())

        assert '_request_id' in response, "Response should include request_id"
        assert response['_request_id'] == 42, \
            f"Request ID should be echoed (42), got {response.get('_request_id')}"

    async def test_request_id_zero_handled(
        self, daemon_process, socket_connection, dbus_proxy
    ):
        """Test that request_id of 0 is handled correctly."""
        reader, writer = socket_connection

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Zero ID Test", "Testing",
            ["action1", "Action"], {}, 30000
        )

        await asyncio.sleep(0.5)

        # Request with ID 0
        import json
        request = {
            'type': 'invoke_action',
            'id': notif_id,
            'action': 'action1',
            '_request_id': 0
        }

        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(response_data.decode().strip())

        assert '_request_id' in response, "Response should include request_id"
        assert response['_request_id'] == 0, "Should echo request_id 0"
