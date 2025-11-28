#!/usr/bin/env python3
"""Test body-markup capability compliance"""

from dasbus.connection import SessionMessageBus
import time

bus = SessionMessageBus()
proxy = bus.get_proxy(
    "org.freedesktop.Notifications",
    "/org/freedesktop/Notifications"
)

print("Testing body-markup capability...")
print()

# Check if body-markup is supported
caps = proxy.GetCapabilities()
if 'body-markup' in caps:
    print("✓ Server claims 'body-markup' support")
else:
    print("✗ Server does not claim 'body-markup' support")
    exit(1)

# Test 1: Basic HTML markup
print("\nTest 1: HTML markup in notification")
markup_body = "This has <b>bold</b>, <i>italic</i>, and <u>underlined</u> text."
id1 = proxy.Notify("test-app", 0, "", "Markup Test", markup_body, [], {}, 5000)
print(f"  Sent notification with markup: {markup_body}")
print(f"  Notification ID: {id1}")
print("  Check: Display should show plain text, but data should preserve markup")
time.sleep(3)

# Test 2: HTML with links
print("\nTest 2: HTML with hyperlinks")
link_body = 'Click <a href="https://example.com">here</a> for more info.'
id2 = proxy.Notify("test-app", 0, "", "Link Test", link_body, [], {}, 5000)
print(f"  Sent notification with link: {link_body}")
print(f"  Notification ID: {id2}")
time.sleep(3)

# Test 3: Mixed content
print("\nTest 3: Mixed markup and entities")
mixed_body = "<b>Important:</b> This message contains &lt;tags&gt; and &amp; symbols."
id3 = proxy.Notify("test-app", 0, "", "Mixed Content", mixed_body, [], {}, 5000)
print(f"  Sent notification with entities: {mixed_body}")
print(f"  Notification ID: {id3}")

print("\n✓ All markup tests completed")
print("Verify that:")
print("  1. Popup displays plain text (no HTML tags visible)")
print("  2. Orca reads plain text (no HTML tags announced)")
print("  3. Socket clients receive original markup (if connected)")
