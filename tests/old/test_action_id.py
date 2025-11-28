#!/usr/bin/env python3
"""
Test that actions are invoked on the correct notification
"""
import asyncio
import json
import os
import sys
from dasbus.connection import SessionMessageBus

async def test_action_on_correct_notification():
    """Test that action invocation targets the correct notification"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        print("Make sure the daemon is running: ../src/waynotify")
        return False

    try:
        # Send multiple notifications with different actions
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("Testing action invocation on correct notification...")
        print()

        print("1. Sending three notifications with different actions...")
        notif_id_1 = notify.Notify(
            "App 1", 0, "dialog-information", "Notification 1",
            "First notification", ["action1", "Action One"], {}, 60000
        )
        print(f"   ✓ Notification {notif_id_1} sent (action1)")

        notif_id_2 = notify.Notify(
            "App 2", 0, "dialog-information", "Notification 2",
            "Second notification", ["action2", "Action Two"], {}, 60000
        )
        print(f"   ✓ Notification {notif_id_2} sent (action2)")

        notif_id_3 = notify.Notify(
            "App 3", 0, "dialog-information", "Notification 3",
            "Third notification", ["action3", "Action Three"], {}, 60000
        )
        print(f"   ✓ Notification {notif_id_3} sent (action3)")
        print()

        # Connect to daemon via socket
        print("2. Connecting to daemon socket...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected to daemon")
        print()

        # Set up D-Bus signal monitoring
        print("3. Setting up D-Bus signal listener...")
        received_signals = []

        def on_action_invoked(notification_id, action_key):
            received_signals.append(('ActionInvoked', notification_id, action_key))
            print(f"   📡 D-Bus ActionInvoked: notif_id={notification_id}, action='{action_key}'")

        # Subscribe to ActionInvoked signal
        notify.ActionInvoked.connect(on_action_invoked)
        print("   ✓ Listening for ActionInvoked signals")
        print()

        # Invoke action on notification 2 (middle one)
        print(f"4. Invoking 'action2' on notification {notif_id_2}...")
        request = {
            'type': 'invoke_action',
            'id': notif_id_2,
            'action': 'action2',
            '_request_id': 1
        }
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        # Wait for response
        response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(response_data.decode().strip())

        if response.get('success'):
            print(f"   ✓ Socket response: success={response.get('success')}")
        else:
            print(f"   ✗ Socket response: {response}")
            return False

        # Wait a bit for D-Bus signal
        await asyncio.sleep(0.5)
        print()

        # Check if correct signal was received
        print("5. Verifying correct notification received the action...")
        if not received_signals:
            print("   ✗ No D-Bus signals received!")
            return False

        signal_type, signal_notif_id, signal_action = received_signals[-1]

        if signal_notif_id == notif_id_2 and signal_action == 'action2':
            print(f"   ✓ CORRECT: Action invoked on notification {notif_id_2} with action 'action2'")
        else:
            print(f"   ✗ WRONG: Expected notif {notif_id_2}/action2, got notif {signal_notif_id}/{signal_action}")
            return False
        print()

        # Clean up
        writer.close()
        await writer.wait_closed()

        print("=" * 60)
        print("TEST RESULT: SUCCESS")
        print("Actions are invoked on the correct notification!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_action_on_correct_notification())
    sys.exit(0 if success else 1)
