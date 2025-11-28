#!/usr/bin/env python3
"""
Test waynotify compliance with freedesktop.org notification specification
https://specifications.freedesktop.org/notification-spec/1.2/
"""

from dasbus.connection import SessionMessageBus
import time

bus = SessionMessageBus()
proxy = bus.get_proxy(
    "org.freedesktop.Notifications",
    "/org/freedesktop/Notifications"
)

print("Testing freedesktop.org notification specification compliance")
print("=" * 70)

# Test 1: GetServerInformation
print("\n1. GetServerInformation")
print("-" * 70)
name, vendor, version, spec_version = proxy.GetServerInformation()
print(f"   Name: {name}")
print(f"   Vendor: {vendor}")
print(f"   Version: {version}")
print(f"   Spec Version: {spec_version}")
assert spec_version == "1.2", f"Spec version should be '1.2', got '{spec_version}'"
print("   ✓ Returns correct spec version 1.2")

# Test 2: GetCapabilities
print("\n2. GetCapabilities")
print("-" * 70)
caps = proxy.GetCapabilities()
print(f"   Capabilities: {caps}")
required_caps = ['actions', 'body']
for cap in required_caps:
    assert cap in caps, f"Missing required capability: {cap}"
print(f"   ✓ Has required capabilities: {required_caps}")

# Test 3: Notify - basic notification
print("\n3. Notify - Basic notification")
print("-" * 70)
id1 = proxy.Notify("test-app", 0, "", "Test Summary", "Test Body", [], {}, -1)
print(f"   Created notification ID: {id1}")
assert id1 > 0, "Notification ID must be greater than 0"
print("   ✓ Returns valid ID > 0")
time.sleep(2)

# Test 4: Notify - replacing notification
print("\n4. Notify - Replace notification (replaces_id)")
print("-" * 70)
id2 = proxy.Notify("test-app", id1, "", "Replaced Summary", "Replaced Body", [], {}, -1)
print(f"   Replacement ID: {id2}")
assert id2 == id1, f"Replacement should return same ID. Expected {id1}, got {id2}"
print(f"   ✓ Correctly returns replaces_id: {id2}")
time.sleep(2)

# Test 5: Notify - replaces_id with non-existent ID
print("\n5. Notify - Replace with non-existent ID")
print("-" * 70)
non_existent_id = 99999
id3 = proxy.Notify("test-app", non_existent_id, "", "Test", "Non-existent replace", [], {}, -1)
print(f"   Tried to replace ID {non_existent_id}, got ID: {id3}")
# According to spec: "If replaces_id is 0, the return value is a UINT32 that represent the notification."
# If replaces_id is non-zero, it should be returned - spec says "atomically replaces"
# This is ambiguous - some implementations create new ID if doesn't exist, others use the provided ID
print(f"   ℹ ID returned: {id3} (implementation-specific behavior)")
time.sleep(2)

# Test 6: Actions
print("\n6. Notify - With actions")
print("-" * 70)
if 'actions' in caps:
    id4 = proxy.Notify("test-app", 0, "", "Action Test", "Click a button",
                       ["default", "Default Action", "cancel", "Cancel"], {}, 5000)
    print(f"   Created notification with actions: ID {id4}")
    print("   ✓ Actions supported")
else:
    print("   ⚠ Actions not supported")
time.sleep(2)

# Test 7: Icon support
print("\n7. Notify - With icon")
print("-" * 70)
id5 = proxy.Notify("test-app", 0, "dialog-information", "Icon Test", "Has an icon", [], {}, -1)
print(f"   Created notification with icon: ID {id5}")
print("   ✓ Icon parameter accepted")
time.sleep(2)

# Test 8: Hints
print("\n8. Notify - With hints")
print("-" * 70)
from dasbus.typing import Variant
hints = {"urgency": Variant("y", 2)}  # Critical urgency (byte type)
id6 = proxy.Notify("test-app", 0, "", "Critical", "Urgent message", [], hints, -1)
print(f"   Created critical notification: ID {id6}")
print("   ✓ Hints parameter accepted")
time.sleep(2)

# Test 9: Expire timeout behavior
print("\n9. Notify - Expire timeout")
print("-" * 70)
# -1 = server default
id7 = proxy.Notify("test-app", 0, "", "Default Timeout", "Should use server default", [], {}, -1)
print(f"   ID {id7}: expire_timeout = -1 (server default)")

# 0 = never expire
id8 = proxy.Notify("test-app", 0, "", "Never Expire", "Should never expire automatically", [], {}, 0)
print(f"   ID {id8}: expire_timeout = 0 (never expire)")

# Specific timeout
id9 = proxy.Notify("test-app", 0, "", "2 Second Timeout", "Expires in 2 seconds", [], {}, 2000)
print(f"   ID {id9}: expire_timeout = 2000 (2 seconds)")
print("   ✓ All timeout modes accepted")

# Test 10: CloseNotification
print("\n10. CloseNotification")
print("-" * 70)
close_id = proxy.Notify("test-app", 0, "", "Will Close", "Closing this notification", [], {}, 0)
print(f"   Created notification ID {close_id}")
time.sleep(1)
proxy.CloseNotification(close_id)
print(f"   Called CloseNotification({close_id})")
print("   ✓ CloseNotification accepted")

# Test 11: Close non-existent notification
print("\n11. CloseNotification - Non-existent ID")
print("-" * 70)
try:
    proxy.CloseNotification(88888)
    print("   ✓ CloseNotification with invalid ID handled gracefully")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n" + "=" * 70)
print("Specification compliance tests completed!")
print("=" * 70)
