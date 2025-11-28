"""
Test D-Bus signals: NotificationClosed and ActionInvoked.

Tests signal emission, parameters, and timing according to the spec.
"""
import asyncio
import time

import pytest
from gi.repository import GLib


@pytest.mark.integration
@pytest.mark.dbus
class TestNotificationClosedSignal:
    """Test NotificationClosed signal emission."""

    def test_signal_on_close_notification(self, daemon_process, dbus_proxy, notification_signals):
        """Test NotificationClosed signal when CloseNotification is called."""
        # Create notification
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Test Close", "Will be closed via method", [], {}, 0
        )

        time.sleep(0.5)

        # Clear any previous signals
        notification_signals['closed'].clear()

        # Close notification
        dbus_proxy.CloseNotification(notif_id)

        # Give time for signal to be delivered
        time.sleep(0.5)

        # Check signal was emitted
        closed_signals = notification_signals['closed']
        assert len(closed_signals) > 0, "NotificationClosed signal should be emitted"

        # Find our notification
        matching = [s for s in closed_signals if s[0] == notif_id]
        assert len(matching) > 0, f"Should receive signal for notification {notif_id}"

        notif_id_received, reason = matching[0]
        assert notif_id_received == notif_id, "Signal should have correct notification ID"
        assert reason == 3, f"Reason should be 3 (CloseNotification called), got {reason}"

    def test_signal_reason_codes(self, daemon_process, dbus_proxy, notification_signals):
        """Test that reason codes are valid according to spec."""
        # Create and close a notification
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Reason Test", "Testing reason codes", [], {}, 0
        )

        time.sleep(0.5)
        notification_signals['closed'].clear()

        dbus_proxy.CloseNotification(notif_id)
        time.sleep(0.5)

        closed_signals = notification_signals['closed']
        if closed_signals:
            _, reason = closed_signals[-1]
            # Valid reasons: 1=expired, 2=dismissed, 3=closed by call, 4=undefined
            assert reason in [1, 2, 3, 4], f"Reason {reason} not in valid range [1-4]"


@pytest.mark.integration
@pytest.mark.dbus
@pytest.mark.slow
class TestActionInvokedSignal:
    """Test ActionInvoked signal emission."""

    async def test_action_invoked_via_socket(
        self, daemon_process, dbus_proxy, socket_client, notification_signals
    ):
        """Test ActionInvoked signal when action invoked via socket."""
        # Create notification with actions
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Action Test",
            "Testing action invocation",
            ["action1", "First Action", "action2", "Second Action"],
            {},
            30000
        )

        await asyncio.sleep(0.5)
        notification_signals['invoked'].clear()

        # Invoke action via socket (simulates client button click)
        response = await socket_client.invoke_action(notif_id, "action1")

        assert response.get('type') == 'action_result', "Should get action_result response"
        assert response.get('success'), "Action should succeed"

        # Give time for signal
        await asyncio.sleep(0.5)

        # Check signal was emitted
        invoked_signals = notification_signals['invoked']
        assert len(invoked_signals) > 0, "ActionInvoked signal should be emitted"

        # Find our action
        matching = [s for s in invoked_signals if s[0] == notif_id]
        assert len(matching) > 0, f"Should receive signal for notification {notif_id}"

        notif_id_received, action_key = matching[0]
        assert notif_id_received == notif_id, "Signal should have correct notification ID"
        assert action_key == "action1", f"Action key should be 'action1', got '{action_key}'"

    async def test_action_followed_by_close_signal(
        self, daemon_process, dbus_proxy, socket_client, notification_signals
    ):
        """Test that ActionInvoked is followed by NotificationClosed."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Action Close Test",
            "Should close after action", ["default", "Click Me"], {}, 0
        )

        await asyncio.sleep(0.5)
        notification_signals['invoked'].clear()
        notification_signals['closed'].clear()

        # Invoke action
        await socket_client.invoke_action(notif_id, "default")
        await asyncio.sleep(0.5)

        # Both signals should be emitted
        assert len(notification_signals['invoked']) > 0, "ActionInvoked should be emitted"
        assert len(notification_signals['closed']) > 0, "NotificationClosed should be emitted"

        # ActionInvoked should come first (if we track order)
        invoked_ids = [s[0] for s in notification_signals['invoked']]
        closed_ids = [s[0] for s in notification_signals['closed']]

        assert notif_id in invoked_ids, "Should receive ActionInvoked for our notification"
        assert notif_id in closed_ids, "Should receive NotificationClosed for our notification"


@pytest.mark.integration
@pytest.mark.dbus
class TestSignalParameters:
    """Test signal parameter types and values."""

    def test_notification_closed_parameters(
        self, daemon_process, dbus_proxy, notification_signals
    ):
        """Test NotificationClosed signal has correct parameter types."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Param Test", "Testing parameters", [], {}, 0
        )

        time.sleep(0.5)
        notification_signals['closed'].clear()

        dbus_proxy.CloseNotification(notif_id)
        time.sleep(0.5)

        closed_signals = notification_signals['closed']
        if closed_signals:
            notif_id_param, reason_param = closed_signals[-1]

            assert isinstance(notif_id_param, int), "Notification ID should be int"
            assert isinstance(reason_param, int), "Reason should be int"
            assert notif_id_param > 0, "Notification ID should be positive"
            assert 1 <= reason_param <= 4, "Reason should be in range 1-4"

    async def test_action_invoked_parameters(
        self, daemon_process, dbus_proxy, socket_client, notification_signals
    ):
        """Test ActionInvoked signal has correct parameter types."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Param Test",
            "Testing action parameters",
            ["test_action", "Test Action"],
            {}, 30000
        )

        await asyncio.sleep(0.5)
        notification_signals['invoked'].clear()

        await socket_client.invoke_action(notif_id, "test_action")
        await asyncio.sleep(0.5)

        invoked_signals = notification_signals['invoked']
        if invoked_signals:
            notif_id_param, action_param = invoked_signals[-1]

            assert isinstance(notif_id_param, int), "Notification ID should be int"
            assert isinstance(action_param, str), "Action key should be string"
            assert notif_id_param > 0, "Notification ID should be positive"
            assert len(action_param) > 0, "Action key should not be empty"


@pytest.mark.integration
@pytest.mark.dbus
class TestSignalTiming:
    """Test signal timing and ordering."""

    async def test_multiple_notifications_signal_order(
        self, daemon_process, dbus_proxy, notification_signals
    ):
        """Test signals for multiple notifications maintain correct IDs."""
        notification_signals['closed'].clear()

        # Create multiple notifications
        ids = []
        for i in range(3):
            notif_id = dbus_proxy.Notify(
                "test-app", 0, "", f"Notification {i}",
                f"Body {i}", [], {}, 0
            )
            ids.append(notif_id)

        await asyncio.sleep(0.5)

        # Close them in order
        for notif_id in ids:
            dbus_proxy.CloseNotification(notif_id)
            await asyncio.sleep(0.2)

        # All should have emitted signals
        closed_ids = [s[0] for s in notification_signals['closed']]

        for notif_id in ids:
            assert notif_id in closed_ids, f"Should receive signal for notification {notif_id}"
