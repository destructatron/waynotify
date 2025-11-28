#!/usr/bin/env python3
"""
Test to reproduce the bug where the first notification doesn't appear in the client
This test simulates a client that connects and stays connected, then a notification arrives
"""
import asyncio
import json
import os
import sys
from dasbus.connection import SessionMessageBus

async def test_connected_client_first_notification():
    """Test client that's already connected when first notification arrives"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        print("Make sure the daemon is running: ./src/waynotify")
        return False

    try:
        # Connect to daemon FIRST (before any notifications)
        print("1. Connecting to daemon socket...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected to daemon")
        print()

        # Create a task to listen for ALL messages (single reader pattern)
        notifications_received = []
        pending_responses = {}
        running = [True]

        async def message_reader():
            while running[0]:
                try:
                    data = await reader.readline()
                    if not data:
                        break
                    message = json.loads(data.decode().strip())

                    # Check if this is a response to a request
                    request_id = message.get('_request_id')
                    if request_id is not None and request_id in pending_responses:
                        future = pending_responses.pop(request_id)
                        future.set_result(message)
                    elif message.get('type') == 'new_notification':
                        print(f"   [PUSH] Received: new_notification")
                        notifications_received.append(message.get('notification'))
                except:
                    break

        reader_task = asyncio.create_task(message_reader())

        # Wait a moment for connection to stabilize
        await asyncio.sleep(0.5)

        # NOW send first notification via D-Bus
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("2. Sending FIRST notification (client already connected)...")
        notif_id = notify.Notify(
            "Test App",
            0,
            "dialog-information",
            "First Notification",
            "This is the first notification body",
            [],
            {},
            10000
        )
        print(f"   ✓ Notification {notif_id} sent")
        print()

        # Wait for push notification to arrive
        print("3. Waiting for push notification...")
        await asyncio.sleep(1.0)

        if len(notifications_received) > 0:
            print(f"   ✓ Received {len(notifications_received)} push notification(s)")
        else:
            print(f"   ✗ No push notifications received!")
        print()

        # Now request the full list (like client does on startup/refresh)
        print("4. Requesting notification list...")
        request_id = 1
        request = {
            'type': 'get_all',
            '_request_id': request_id
        }

        # Create future for response
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        pending_responses[request_id] = future

        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        # Wait for response via future
        print("5. Waiting for list response...")
        response = await asyncio.wait_for(future, timeout=5.0)

        running[0] = False
        reader_task.cancel()

        if response.get('type') == 'notification_list':
            notifications = response.get('notifications', [])
            print(f"   ✓ Received notification list with {len(notifications)} notification(s)")
            print()

            if len(notifications) == 0:
                print("✗ ERROR: No notifications in list!")
                print("The first notification is missing!")
                print()
                return False

            if len(notifications) > 0:
                print("Notifications in list:")
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
                print(f"✓ SUCCESS: First notification {notif_id} is in the list!")
                return True
            else:
                print(f"✗ FAIL: First notification {notif_id} NOT in list!")
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
            running[0] = False
            reader_task.cancel()
        except:
            pass
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

if __name__ == '__main__':
    success = asyncio.run(test_connected_client_first_notification())
    sys.exit(0 if success else 1)
