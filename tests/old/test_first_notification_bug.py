#!/usr/bin/env python3
"""
Test to reproduce the bug where the first notification doesn't appear in the client
"""
import asyncio
import json
import os
import sys
from dasbus.connection import SessionMessageBus

async def test_first_notification():
    """Test that the first notification appears when requesting the list"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        print("Make sure the daemon is running: ./src/waynotify")
        return False

    try:
        # Send first notification via D-Bus
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("1. Sending first notification via D-Bus...")
        notif_id = notify.Notify(
            "Test App",
            0,
            "dialog-information",
            "First Notification",
            "This is the first notification body",
            [],
            {},
            5000
        )
        print(f"   ✓ Notification {notif_id} sent")
        print()

        # Wait a moment for the notification to be processed
        await asyncio.sleep(0.5)

        # Connect to daemon via socket (like the client does)
        print("2. Connecting to daemon socket...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected to daemon")
        print()

        # Request all notifications (like the client does)
        print("3. Requesting all notifications...")
        request = {
            'type': 'get_all',
            '_request_id': 1
        }
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()
        print("   ✓ Request sent")
        print()

        # Wait for response
        print("4. Waiting for response...")
        response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(response_data.decode().strip())

        if response.get('type') == 'notification_list':
            notifications = response.get('notifications', [])
            print(f"   ✓ Received notification list with {len(notifications)} notification(s)")
            print()

            if len(notifications) == 0:
                print("ERROR: No notifications returned!")
                print("Expected 1 notification but got 0")
                print()
                return False

            if len(notifications) > 0:
                print("Notifications received:")
                for notif in notifications:
                    print(f"   - ID: {notif['id']}, Summary: {notif['summary']}")
                print()

            # Check if our notification is in the list
            found = False
            for notif in notifications:
                if notif['id'] == notif_id:
                    found = True
                    break

            if found:
                print(f"✓ SUCCESS: Notification {notif_id} found in list!")
                return True
            else:
                print(f"✗ FAIL: Notification {notif_id} NOT found in list!")
                print(f"List contains IDs: {[n['id'] for n in notifications]}")
                return False
        else:
            print(f"   ✗ Unexpected response: {response}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

if __name__ == '__main__':
    success = asyncio.run(test_first_notification())
    sys.exit(0 if success else 1)
