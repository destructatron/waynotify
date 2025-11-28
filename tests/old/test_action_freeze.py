#!/usr/bin/env python3
"""
Test script to verify notification actions don't freeze the daemon
"""
import time
import sys
from dasbus.connection import SessionMessageBus

def test_action_freeze():
    """Test that invoking actions doesn't freeze the daemon"""
    try:
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("Testing notification action handling...")
        print()

        # Test 1: Send notification with action
        print("1. Sending notification with action button...")
        notif_id = notify.Notify(
            "Action Test",  # app_name
            0,  # replaces_id
            "",  # app_icon
            "Click the Action Button",  # summary
            "Please click the 'Test Action' button in the popup",  # body
            ["test", "Test Action", "cancel", "Cancel"],  # actions
            {},  # hints
            10000  # expire_timeout (10 seconds)
        )
        print(f"   Notification {notif_id} sent - PLEASE CLICK THE ACTION BUTTON")
        print()

        # Wait for user to click
        print("2. Waiting 12 seconds for you to click the action...")
        time.sleep(12)

        # Test 2: Check if daemon is still responsive
        print()
        print("3. Testing if daemon is still responsive...")
        try:
            # Try to get server info - if this hangs, daemon is frozen
            info = notify.GetServerInformation()
            print(f"   ✓ Daemon responsive! Server: {info[0]} v{info[2]}")
        except Exception as e:
            print(f"   ✗ Daemon NOT responsive! Error: {e}")
            return False

        # Test 3: Send another notification to verify display still works
        print()
        print("4. Sending follow-up notification...")
        notif_id2 = notify.Notify(
            "Follow-up Test",
            0,
            "",
            "Success!",
            "If you see this popup, the daemon is working correctly",
            [],
            {},
            5000
        )
        print(f"   ✓ Notification {notif_id2} sent successfully")
        print()

        print("=" * 60)
        print("TEST RESULT: SUCCESS")
        print("The daemon remained responsive after action invocation!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"Error: {e}")
        print()
        print("Make sure the daemon is running: ./waynotify")
        return False

if __name__ == '__main__':
    success = test_action_freeze()
    sys.exit(0 if success else 1)
