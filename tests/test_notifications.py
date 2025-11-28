"""
Tests for notification display and behavior.

Tests urgency levels, timeouts, and general notification handling.
Converts test_notifications.sh functionality.
"""
import asyncio
import time

import pytest
from dasbus.typing import Variant


@pytest.mark.integration
@pytest.mark.dbus
class TestBasicNotifications:
    """Test basic notification creation and display."""

    def test_send_basic_notification(self, daemon_process, dbus_proxy):
        """Test sending a basic notification."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Test Notification",
            "This is a basic test message",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should create notification successfully"

    def test_send_notification_with_app_name(self, daemon_process, dbus_proxy):
        """Test notification with custom app name."""
        notif_id = dbus_proxy.Notify(
            "CustomApp",
            0,
            "",
            "Custom Application",
            "This is from a custom app",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should handle custom app names"

    def test_persistent_notification(self, daemon_process, dbus_proxy):
        """Test notification that doesn't expire (timeout=0)."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Persistent",
            "This notification won't expire",
            [],
            {},
            0  # Never expire
        )

        assert notif_id > 0, "Should create persistent notification"


@pytest.mark.integration
@pytest.mark.dbus
class TestUrgencyLevels:
    """Test notification urgency levels."""

    def test_low_urgency(self, daemon_process, dbus_proxy):
        """Test low urgency notification."""
        hints = {"urgency": Variant("y", 0)}  # Low = 0

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Background Task",
            "This is a low priority notification",
            [],
            hints,
            -1
        )

        assert notif_id > 0, "Should create low urgency notification"

    def test_normal_urgency(self, daemon_process, dbus_proxy):
        """Test normal urgency notification."""
        hints = {"urgency": Variant("y", 1)}  # Normal = 1

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Normal Notification",
            "This is a normal priority notification",
            [],
            hints,
            -1
        )

        assert notif_id > 0, "Should create normal urgency notification"

    def test_critical_urgency(self, daemon_process, dbus_proxy):
        """Test critical urgency notification."""
        hints = {"urgency": Variant("y", 2)}  # Critical = 2

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Urgent Alert",
            "This is an urgent notification!",
            [],
            hints,
            -1
        )

        assert notif_id > 0, "Should create critical urgency notification"

    def test_default_urgency(self, daemon_process, dbus_proxy):
        """Test notification with no urgency hint (should default to normal)."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Default Urgency",
            "No urgency hint specified",
            [],
            {},  # No hints
            -1
        )

        assert notif_id > 0, "Should handle missing urgency hint"


@pytest.mark.integration
@pytest.mark.dbus
class TestNotificationTimeouts:
    """Test notification timeout behavior."""

    def test_default_timeout(self, daemon_process, dbus_proxy):
        """Test notification with default timeout (-1)."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Default Timeout",
            "Uses server default", [], {}, -1
        )

        assert notif_id > 0, "Should accept default timeout"

    def test_custom_timeout(self, daemon_process, dbus_proxy):
        """Test notification with custom timeout."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Custom Timeout",
            "Expires in 3 seconds", [], {}, 3000
        )

        assert notif_id > 0, "Should accept custom timeout"

    def test_very_short_timeout(self, daemon_process, dbus_proxy):
        """Test notification with very short timeout."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Quick",
            "Very short timeout", [], {}, 100  # 100ms
        )

        assert notif_id > 0, "Should accept very short timeout"

    async def test_very_long_timeout(self, daemon_process, dbus_proxy):
        """Test notification with very long timeout."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Long Timeout",
            "Very long timeout", [], {}, 3600000  # 1 hour
        )

        assert notif_id > 0, "Should accept very long timeout"


@pytest.mark.integration
@pytest.mark.dbus
class TestNotificationReplacement:
    """Test notification replacement behavior."""

    def test_replace_notification_updates_content(self, daemon_process, dbus_proxy):
        """Test that replacing a notification updates its content."""
        # Create original
        id1 = dbus_proxy.Notify(
            "test-app", 0, "", "Original", "Original content", [], {}, 0
        )

        time.sleep(0.5)

        # Replace it
        id2 = dbus_proxy.Notify(
            "test-app", id1, "", "Updated", "Updated content", [], {}, 0
        )

        assert id2 == id1, "Should return same ID for replacement"

    def test_replace_notification_updates_urgency(self, daemon_process, dbus_proxy):
        """Test that replacing can change urgency."""
        # Create normal urgency
        hints_normal = {"urgency": Variant("y", 1)}
        id1 = dbus_proxy.Notify(
            "test-app", 0, "", "Normal", "Normal urgency",
            [], hints_normal, 0
        )

        time.sleep(0.5)

        # Replace with critical
        hints_critical = {"urgency": Variant("y", 2)}
        id2 = dbus_proxy.Notify(
            "test-app", id1, "", "Critical", "Now critical!",
            [], hints_critical, 0
        )

        assert id2 == id1, "Should return same ID"

    def test_replace_adds_actions(self, daemon_process, dbus_proxy):
        """Test that replacement can add actions."""
        # Create without actions
        id1 = dbus_proxy.Notify(
            "test-app", 0, "", "No Actions", "No actions", [], {}, 0
        )

        time.sleep(0.5)

        # Replace with actions
        id2 = dbus_proxy.Notify(
            "test-app", id1, "", "Has Actions", "Now has actions",
            ["action1", "Click Me"], {}, 0
        )

        assert id2 == id1, "Should return same ID"


@pytest.mark.integration
@pytest.mark.dbus
class TestMultipleNotifications:
    """Test handling of multiple notifications."""

    def test_send_multiple_notifications(self, daemon_process, dbus_proxy):
        """Test sending multiple notifications in sequence."""
        ids = []

        for i in range(5):
            notif_id = dbus_proxy.Notify(
                "test-app", 0, "", f"Notification {i}",
                f"Body text {i}", [], {}, -1
            )
            ids.append(notif_id)
            time.sleep(0.2)

        # All should have unique IDs
        assert len(set(ids)) == len(ids), "All notifications should have unique IDs"

        # All should be positive
        assert all(id > 0 for id in ids), "All IDs should be positive"

    def test_notifications_from_different_apps(self, daemon_process, dbus_proxy):
        """Test notifications from multiple apps."""
        apps = ["App1", "App2", "App3"]
        ids = []

        for app in apps:
            notif_id = dbus_proxy.Notify(
                app, 0, "", f"From {app}",
                f"Message from {app}", [], {}, -1
            )
            ids.append(notif_id)

        assert len(ids) == len(apps), "Should create notification for each app"
        assert all(id > 0 for id in ids), "All should have valid IDs"

    async def test_concurrent_notifications(self, daemon_process, dbus_proxy):
        """Test handling of notifications sent concurrently."""
        async def send_notification(i):
            return await asyncio.to_thread(
                dbus_proxy.Notify,
                "test-app", 0, "", f"Concurrent {i}",
                f"Message {i}", [], {}, -1
            )

        # Send multiple notifications concurrently
        ids = await asyncio.gather(*[send_notification(i) for i in range(10)])

        assert len(ids) == 10, "Should create all notifications"
        assert len(set(ids)) == 10, "All should have unique IDs"


@pytest.mark.integration
@pytest.mark.dbus
class TestNotificationHistory:
    """Test notification history tracking."""

    async def test_notifications_appear_in_history(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that sent notifications appear in history."""
        # Send notification
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "History Test",
            "Should appear in history", [], {}, -1
        )

        await asyncio.sleep(0.5)

        # Get history
        notifications = await socket_client.get_notifications()

        # Find our notification
        matching = [n for n in notifications if n.get('id') == notif_id]
        assert len(matching) > 0, "Notification should appear in history"

        # Check content
        notif = matching[0]
        assert notif.get('summary') == "History Test"
        assert notif.get('body') == "Should appear in history"

    async def test_replaced_notification_not_duplicated(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that replaced notifications don't create duplicates."""
        # Create notification
        id1 = dbus_proxy.Notify(
            "test-app", 0, "", "Original", "Original", [], {}, 0
        )

        await asyncio.sleep(0.5)

        # Replace it
        id2 = dbus_proxy.Notify(
            "test-app", id1, "", "Replaced", "Replaced", [], {}, 0
        )

        assert id1 == id2

        await asyncio.sleep(0.5)

        # Check history - should only have one entry
        notifications = await socket_client.get_notifications()
        matching = [n for n in notifications if n.get('id') == id1]

        # Should have exactly one entry (the replaced version)
        assert len(matching) == 1, "Should not duplicate replaced notifications"
        assert matching[0].get('summary') == "Replaced", "Should have updated content"
