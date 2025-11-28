#!/usr/bin/env python3
"""
Test client action invocation to verify it doesn't freeze the daemon
Tests the socket-based action invocation path (not popup button clicks)
"""
import asyncio
import json
import os
import sys
from dasbus.connection import SessionMessageBus

async def test_client_action():
    """Test that client-invoked actions don't freeze the daemon"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        print("Make sure the daemon is running: ../src/waynotify")
        return False

    try:
        # First, send a notification with actions via D-Bus
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("Testing client action invocation...")
        print()

        print("1. Sending notification with actions...")
        notif_id = notify.Notify(
            "Client Action Test",
            0,
            "dialog-information",
            "Action Test",
            "Testing client-triggered action invocation",
            ["action1", "First Action", "action2", "Second Action"],
            {},
            30000  # 30 second timeout
        )
        print(f"   ✓ Notification {notif_id} sent")
        print()

        # Connect to daemon via socket
        print("2. Connecting to daemon socket...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected to daemon")
        print()

        # Invoke action via socket (this is what the client does)
        print("3. Invoking action via socket...")
        request = {
            'type': 'invoke_action',
            'id': notif_id,
            'action': 'action1',
            '_request_id': 1
        }
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()
        print("   ✓ Action request sent")

        # Wait for response with timeout
        print("4. Waiting for daemon response (5 second timeout)...")
        try:
            response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
            response = json.loads(response_data.decode().strip())

            if response.get('type') == 'action_result' and response.get('success'):
                print("   ✓ Got successful response from daemon!")
            else:
                print(f"   ✗ Unexpected response: {response}")
                return False

        except asyncio.TimeoutError:
            print("   ✗ TIMEOUT: Daemon did not respond (still frozen!)")
            return False
        print()

        # Test 5: Verify daemon is still responsive
        print("5. Testing daemon responsiveness...")
        try:
            info = notify.GetServerInformation()
            print(f"   ✓ Daemon responsive! Server: {info[0]} v{info[2]}")
        except Exception as e:
            print(f"   ✗ Daemon not responsive: {e}")
            return False
        print()

        # Test 6: Send another notification to verify display still works
        print("6. Sending follow-up notification...")
        notif_id2 = notify.Notify(
            "Follow-up Test",
            0,
            "dialog-information",
            "Success!",
            "If you see this popup, the daemon recovered correctly",
            [],
            {},
            5000
        )
        print(f"   ✓ Notification {notif_id2} sent successfully")
        print()

        # Clean up
        writer.close()
        await writer.wait_closed()

        print("=" * 60)
        print("TEST RESULT: SUCCESS")
        print("Client action invocation works without freezing!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_client_action())
    sys.exit(0 if success else 1)
