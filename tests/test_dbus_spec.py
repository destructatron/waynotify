"""
Test freedesktop.org notification specification compliance.

Tests D-Bus methods, parameters, and behavior according to:
https://specifications.freedesktop.org/notification-spec/1.2/
"""
import time

import pytest
from dasbus.typing import Variant


@pytest.mark.integration
@pytest.mark.dbus
class TestServerInformation:
    """Test GetServerInformation method."""

    def test_get_server_information(self, daemon_process, dbus_proxy):
        """Test GetServerInformation returns correct values."""
        name, vendor, version, spec_version = dbus_proxy.GetServerInformation()

        assert isinstance(name, str), "Name should be a string"
        assert isinstance(vendor, str), "Vendor should be a string"
        assert isinstance(version, str), "Version should be a string"
        assert isinstance(spec_version, str), "Spec version should be a string"

        assert name == "WayNotify", f"Expected name 'WayNotify', got '{name}'"
        assert spec_version == "1.2", f"Spec version should be '1.2', got '{spec_version}'"


@pytest.mark.integration
@pytest.mark.dbus
class TestCapabilities:
    """Test GetCapabilities method."""

    def test_get_capabilities(self, daemon_process, dbus_proxy):
        """Test GetCapabilities returns required capabilities."""
        caps = dbus_proxy.GetCapabilities()

        assert isinstance(caps, list), "Capabilities should be a list"
        assert len(caps) > 0, "Should report at least some capabilities"

        # Required capabilities
        required_caps = ['actions', 'body']
        for cap in required_caps:
            assert cap in caps, f"Missing required capability: {cap}"

    def test_capabilities_content(self, daemon_process, dbus_proxy):
        """Test that capabilities match implementation features."""
        caps = dbus_proxy.GetCapabilities()

        # WayNotify should support these
        expected_caps = ['actions', 'body', 'body-markup']
        for cap in expected_caps:
            assert cap in caps, f"Expected capability not found: {cap}"


@pytest.mark.integration
@pytest.mark.dbus
class TestNotify:
    """Test Notify method and notification creation."""

    def test_notify_basic(self, daemon_process, dbus_proxy):
        """Test basic notification creation."""
        notif_id = dbus_proxy.Notify(
            "test-app",  # app_name
            0,           # replaces_id
            "",          # app_icon
            "Test Summary",
            "Test Body",
            [],          # actions
            {},          # hints
            -1           # expire_timeout
        )

        assert isinstance(notif_id, int), "Notification ID should be an integer"
        assert notif_id > 0, "Notification ID should be greater than 0"

    def test_notify_replaces_id(self, daemon_process, dbus_proxy):
        """Test notification replacement with replaces_id."""
        # Create initial notification
        id1 = dbus_proxy.Notify("test-app", 0, "", "Original", "Original body", [], {}, -1)
        assert id1 > 0

        time.sleep(0.5)

        # Replace it
        id2 = dbus_proxy.Notify("test-app", id1, "", "Replaced", "Replaced body", [], {}, -1)

        assert id2 == id1, f"Replacement should return same ID. Expected {id1}, got {id2}"

    def test_notify_replaces_nonexistent(self, daemon_process, dbus_proxy):
        """Test notification replacement with non-existent ID."""
        non_existent_id = 99999
        new_id = dbus_proxy.Notify(
            "test-app",
            non_existent_id,
            "",
            "Test",
            "Non-existent replace",
            [],
            {},
            -1
        )

        # Implementation-specific: some create new ID, some use provided ID
        assert isinstance(new_id, int), "Should return an integer ID"
        assert new_id > 0, "ID should be positive"

    def test_notify_with_icon(self, daemon_process, dbus_proxy):
        """Test notification with icon parameter."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "dialog-information",  # app_icon
            "Icon Test",
            "Has an icon",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should create notification with icon"

    def test_notify_with_actions(self, daemon_process, dbus_proxy):
        """Test notification with actions."""
        caps = dbus_proxy.GetCapabilities()

        if 'actions' not in caps:
            pytest.skip("Actions not supported")

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Action Test",
            "Click a button",
            ["default", "Default Action", "cancel", "Cancel"],
            {},
            5000
        )

        assert notif_id > 0, "Should create notification with actions"

    def test_notify_with_hints(self, daemon_process, dbus_proxy):
        """Test notification with hints."""
        hints = {
            "urgency": Variant("y", 2)  # Critical urgency (byte type)
        }

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",
            "Critical",
            "Urgent message",
            [],
            hints,
            -1
        )

        assert notif_id > 0, "Should create notification with hints"

    def test_notify_expire_timeout_default(self, daemon_process, dbus_proxy):
        """Test notification with default timeout (-1)."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Default Timeout",
            "Should use server default", [], {}, -1
        )

        assert notif_id > 0, "Should accept -1 (server default)"

    def test_notify_expire_timeout_never(self, daemon_process, dbus_proxy):
        """Test notification that never expires (0)."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Never Expire",
            "Should never expire automatically", [], {}, 0
        )

        assert notif_id > 0, "Should accept 0 (never expire)"

    def test_notify_expire_timeout_specific(self, daemon_process, dbus_proxy):
        """Test notification with specific timeout."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "2 Second Timeout",
            "Expires in 2 seconds", [], {}, 2000
        )

        assert notif_id > 0, "Should accept specific timeout in milliseconds"


@pytest.mark.integration
@pytest.mark.dbus
class TestCloseNotification:
    """Test CloseNotification method."""

    def test_close_notification(self, daemon_process, dbus_proxy):
        """Test closing an existing notification."""
        # Create notification
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Will Close",
            "Closing this notification", [], {}, 0
        )

        time.sleep(0.5)

        # Should not raise exception
        dbus_proxy.CloseNotification(notif_id)

    def test_close_nonexistent_notification(self, daemon_process, dbus_proxy):
        """Test closing non-existent notification."""
        # Should handle gracefully without raising exception
        try:
            dbus_proxy.CloseNotification(88888)
        except Exception as e:
            pytest.fail(f"Should handle invalid ID gracefully: {e}")

    def test_close_zero_id(self, daemon_process, dbus_proxy):
        """Test closing notification with ID 0."""
        # ID 0 is special (means "don't replace"), should handle gracefully
        try:
            dbus_proxy.CloseNotification(0)
        except Exception as e:
            pytest.fail(f"Should handle ID 0 gracefully: {e}")


@pytest.mark.integration
@pytest.mark.dbus
class TestParameterValidation:
    """Test parameter validation and edge cases."""

    def test_empty_summary(self, daemon_process, dbus_proxy):
        """Test notification with empty summary."""
        notif_id = dbus_proxy.Notify("test-app", 0, "", "", "Body text", [], {}, -1)
        assert notif_id > 0, "Should accept empty summary"

    def test_empty_body(self, daemon_process, dbus_proxy):
        """Test notification with empty body."""
        notif_id = dbus_proxy.Notify("test-app", 0, "", "Summary", "", [], {}, -1)
        assert notif_id > 0, "Should accept empty body"

    def test_long_text(self, daemon_process, dbus_proxy):
        """Test notification with long text."""
        long_summary = "A" * 500
        long_body = "B" * 2000

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", long_summary, long_body, [], {}, -1
        )
        assert notif_id > 0, "Should handle long text"

    def test_unicode_text(self, daemon_process, dbus_proxy):
        """Test notification with Unicode characters."""
        notif_id = dbus_proxy.Notify(
            "test-app", 0, "",
            "Unicode Test 🚀",
            "Text with émojis and spëcial çhars: 你好 🌍",
            [], {}, -1
        )
        assert notif_id > 0, "Should handle Unicode text"
