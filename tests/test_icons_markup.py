"""
Tests for icon support and body markup.

Tests icon display from various sources and HTML markup handling.
Converts test_icon_support.sh and test_markup.py functionality.
"""
import os

import pytest


@pytest.mark.integration
@pytest.mark.dbus
class TestIconSupport:
    """Test notification icon display from various sources."""

    def test_icon_from_theme_name(self, daemon_process, dbus_proxy):
        """Test icon specified by theme name."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "dialog-information",  # Theme icon name
            "Icon Theme",
            "This uses a theme icon",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should accept theme icon name"

    def test_icon_standard_icons(self, daemon_process, dbus_proxy):
        """Test various standard icon names."""
        standard_icons = [
            "dialog-information",
            "dialog-warning",
            "dialog-error",
            "dialog-question",
            "system-software-update",
            "network-wireless"
        ]

        for icon_name in standard_icons:
            notif_id = dbus_proxy.Notify(
                "test-app", 0, icon_name,
                f"Icon: {icon_name}",
                f"Testing {icon_name}",
                [], {}, -1
            )
            assert notif_id > 0, f"Should handle icon {icon_name}"

    def test_icon_from_file_path(self, daemon_process, dbus_proxy):
        """Test icon specified by absolute file path."""
        # Use common icon file if available
        icon_paths = [
            "/usr/share/pixmaps/debian-logo.png",
            "/usr/share/icons/hicolor/48x48/apps/python.png",
            "/usr/share/pixmaps/python.xpm"
        ]

        # Find first available icon
        available_icon = None
        for path in icon_paths:
            if os.path.exists(path):
                available_icon = path
                break

        if not available_icon:
            pytest.skip("No test icon files available")

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            available_icon,  # Absolute file path
            "File Path Icon",
            "This uses an absolute file path",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should accept file path icon"

    def test_icon_from_file_uri(self, daemon_process, dbus_proxy):
        """Test icon specified by file:// URI."""
        # Find available icon
        icon_paths = [
            "/usr/share/pixmaps/debian-logo.png",
            "/usr/share/icons/hicolor/48x48/apps/python.png"
        ]

        available_icon = None
        for path in icon_paths:
            if os.path.exists(path):
                available_icon = path
                break

        if not available_icon:
            pytest.skip("No test icon files available")

        file_uri = f"file://{available_icon}"

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            file_uri,  # file:// URI
            "File URI Icon",
            "This uses a file:// URI",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should accept file:// URI icon"

    def test_notification_without_icon(self, daemon_process, dbus_proxy):
        """Test notification with no icon."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "",  # Empty icon
            "No Icon",
            "This notification has no icon",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should handle notifications without icons"

    def test_icons_with_urgency_levels(self, daemon_process, dbus_proxy):
        """Test icons at different urgency levels."""
        from dasbus.typing import Variant

        urgency_tests = [
            (0, "dialog-information", "Low Priority", "Low urgency with icon"),
            (1, "dialog-warning", "Normal Priority", "Normal urgency with icon"),
            (2, "dialog-error", "Critical Priority", "Critical urgency with icon"),
        ]

        for urgency, icon, summary, body in urgency_tests:
            hints = {"urgency": Variant("y", urgency)}

            notif_id = dbus_proxy.Notify(
                "test-app", 0, icon, summary, body, [], hints, -1
            )

            assert notif_id > 0, f"Should display icon at urgency {urgency}"

    def test_invalid_icon_path(self, daemon_process, dbus_proxy):
        """Test that invalid icon paths are handled gracefully."""
        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "/nonexistent/path/to/icon.png",
            "Invalid Icon",
            "Icon path doesn't exist",
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should handle invalid icon paths gracefully"

    def test_icon_with_special_characters(self, daemon_process, dbus_proxy):
        """Test icon names with special characters."""
        # Some theme icons have hyphens and numbers
        special_icons = [
            "audio-volume-high",
            "network-wireless-0",
            "battery-level-50",
        ]

        for icon_name in special_icons:
            notif_id = dbus_proxy.Notify(
                "test-app", 0, icon_name,
                "Special Icon", f"Testing {icon_name}",
                [], {}, -1
            )
            assert notif_id > 0, f"Should handle icon name: {icon_name}"


@pytest.mark.integration
@pytest.mark.dbus
class TestBodyMarkup:
    """Test body-markup capability and HTML markup handling."""

    def test_body_markup_capability(self, daemon_process, dbus_proxy):
        """Test that server advertises body-markup capability."""
        caps = dbus_proxy.GetCapabilities()

        assert 'body-markup' in caps, \
            "Server should advertise 'body-markup' capability"

    def test_basic_html_markup(self, daemon_process, dbus_proxy):
        """Test notification with basic HTML markup."""
        markup_body = "This has <b>bold</b>, <i>italic</i>, and <u>underlined</u> text."

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Markup Test",
            markup_body, [], {}, -1
        )

        assert notif_id > 0, "Should accept HTML markup in body"

    def test_html_with_hyperlinks(self, daemon_process, dbus_proxy):
        """Test notification with hyperlinks."""
        link_body = 'Click <a href="https://example.com">here</a> for more info.'

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Link Test",
            link_body, [], {}, -1
        )

        assert notif_id > 0, "Should accept hyperlinks in markup"

    def test_html_entities(self, daemon_process, dbus_proxy):
        """Test notification with HTML entities."""
        entity_body = "Contains &lt;tags&gt;, &amp; symbols, and &quot;quotes&quot;."

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Entities Test",
            entity_body, [], {}, -1
        )

        assert notif_id > 0, "Should accept HTML entities"

    def test_mixed_markup_and_entities(self, daemon_process, dbus_proxy):
        """Test notification with mixed markup and entities."""
        mixed_body = "<b>Important:</b> This message contains &lt;tags&gt; and &amp; symbols."

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Mixed Content",
            mixed_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle mixed markup and entities"

    def test_multiline_markup(self, daemon_process, dbus_proxy):
        """Test notification with multiline markup."""
        multiline_body = """<b>Line 1: Bold</b>
<i>Line 2: Italic</i>
<u>Line 3: Underlined</u>"""

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Multiline Markup",
            multiline_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle multiline markup"

    def test_nested_markup(self, daemon_process, dbus_proxy):
        """Test notification with nested HTML tags."""
        nested_body = "<b>Bold with <i>italic inside</i> and <u>underline</u></b>"

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Nested Markup",
            nested_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle nested markup"

    def test_markup_with_line_breaks(self, daemon_process, dbus_proxy):
        """Test notification with <br> tags."""
        br_body = "First line<br>Second line<br><br>Fourth line (double break)"

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Line Breaks",
            br_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle <br> tags"

    def test_malformed_markup(self, daemon_process, dbus_proxy):
        """Test that malformed HTML is handled gracefully."""
        malformed_tests = [
            "<b>Unclosed bold tag",
            "Unopened closing tag</b>",
            "<b><i>Crossed tags</b></i>",
            "<<double brackets>>",
        ]

        for malformed in malformed_tests:
            notif_id = dbus_proxy.Notify(
                "test-app", 0, "", "Malformed Markup",
                malformed, [], {}, -1
            )
            assert notif_id > 0, f"Should handle malformed markup: {malformed}"

    def test_empty_tags(self, daemon_process, dbus_proxy):
        """Test notification with empty HTML tags."""
        empty_body = "Text with <b></b> empty <i></i> tags"

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Empty Tags",
            empty_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle empty HTML tags"

    def test_markup_with_special_characters(self, daemon_process, dbus_proxy):
        """Test markup with Unicode and special characters."""
        special_body = "<b>Unicode:</b> 🚀 你好 <i>émojis</i> and spëcial çhars"

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Special Characters",
            special_body, [], {}, -1
        )

        assert notif_id > 0, "Should handle markup with Unicode"

    async def test_markup_sanitization_in_history(
        self, daemon_process, dbus_proxy, socket_client
    ):
        """Test that markup is properly handled when retrieved via socket."""
        markup_body = "This has <b>bold</b> and <i>italic</i> text."

        notif_id = dbus_proxy.Notify(
            "test-app", 0, "", "Markup Sanitization",
            markup_body, [], {}, -1
        )

        import asyncio
        await asyncio.sleep(0.5)

        # Get notification from history
        notifications = await socket_client.get_notifications()
        matching = [n for n in notifications if n.get('id') == notif_id]

        assert len(matching) > 0, "Should find notification in history"

        # Check that body is included (implementation-specific whether sanitized)
        notif = matching[0]
        assert 'body' in notif, "Notification should have body field"
        assert len(notif['body']) > 0, "Body should not be empty"


@pytest.mark.integration
@pytest.mark.dbus
class TestIconAndMarkupCombination:
    """Test combining icons with markup."""

    def test_icon_with_markup(self, daemon_process, dbus_proxy):
        """Test notification with both icon and markup."""
        markup_body = "<b>Bold text</b> with <i>markup</i>"

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "dialog-information",
            "Icon and Markup",
            markup_body,
            [],
            {},
            -1
        )

        assert notif_id > 0, "Should handle icon with markup body"

    def test_icon_markup_and_actions(self, daemon_process, dbus_proxy):
        """Test notification with icon, markup, and actions."""
        markup_body = "Click <b>below</b> to continue"

        notif_id = dbus_proxy.Notify(
            "test-app",
            0,
            "dialog-question",
            "Full Featured",
            markup_body,
            ["action1", "Continue", "cancel", "Cancel"],
            {},
            -1
        )

        assert notif_id > 0, "Should handle icon, markup, and actions together"
