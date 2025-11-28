#!/usr/bin/env python3
"""
Test that actions work even after the popup has expired.
This simulates the scenario where:
1. A notification popup expires (after 5 seconds)
2. User opens client later and clicks the action
3. The action should still work

This is the Discord use case: notification arrives, popup disappears,
user opens waynotify-client and clicks "Open Channel".
"""
import asyncio
import json
import os
import sys
import time
from dasbus.connection import SessionMessageBus

async def test_delayed_action():
    """Test that action invocation works after popup expires"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        print("Make sure the daemon is running: ../src/waynotify")
        return False

    try:
        bus = SessionMessageBus()
        notify = bus.get_proxy(
            "org.freedesktop.Notifications",
            "/org/freedesktop/Notifications"
        )

        print("Testing delayed action invocation (after popup expires)...")
        print()

        # Set up signal monitoring
        received_signals = []

        def on_action_invoked(notification_id, action_key):
            received_signals.append(('ActionInvoked', notification_id, action_key))
            print(f"   ✓ Received ActionInvoked: notif_id={notification_id}, action='{action_key}'")

        def on_notification_closed(notification_id, reason):
            reasons = {1: 'Expired', 2: 'Dismissed by user', 3: 'Closed by call', 4: 'Undefined'}
            received_signals.append(('NotificationClosed', notification_id, reason))
            print(f"   📡 Received NotificationClosed: notif_id={notification_id}, reason={reason} ({reasons.get(reason, 'Unknown')})")

        notify.ActionInvoked.connect(on_action_invoked)
        notify.NotificationClosed.connect(on_notification_closed)

        print("1. Sending notification with 2-second expiration...")
        notif_id = notify.Notify(
            "Discord",
            0,
            "discord",
            "New Message from Friend",
            "Click to open the channel",
            ["default", "Open Channel"],
            {},
            2000  # 2 second expiration (shorter for testing)
        )
        print(f"   ✓ Notification {notif_id} sent")
        print()

        print("2. Waiting 3 seconds for popup to expire...")
        await asyncio.sleep(3)
        print("   ✓ Popup should have expired by now")
        print()

        print("3. Signals received so far:")
        for signal in received_signals:
            print(f"   - {signal}")
        print()

        # Check if NotificationClosed was emitted on expiration
        closed_signals = [s for s in received_signals if s[0] == 'NotificationClosed']
        if closed_signals:
            print(f"   ⚠️  WARNING: NotificationClosed already emitted! Applications may have cleaned up.")
            print(f"   ⚠️  This is the BUG: Popup expiration emits NotificationClosed, telling apps the notification is done.")
            print()

        # Connect to daemon via socket
        print("4. Connecting to daemon socket (simulating user opening client)...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected")
        print()

        # Clear signal list for this part of the test
        action_signals_before = len([s for s in received_signals if s[0] == 'ActionInvoked'])

        print(f"5. Invoking 'default' action on notification {notif_id}...")
        request = {
            'type': 'invoke_action',
            'id': notif_id,
            'action': 'default',
            '_request_id': 1
        }
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        response_data = await asyncio.wait_for(reader.readline(), timeout=5.0)
        response = json.loads(response_data.decode().strip())

        if response.get('success'):
            print(f"   ✓ Socket response: success=True")
        else:
            print(f"   ✗ Socket response: {response}")
            return False

        # Wait for D-Bus signal
        await asyncio.sleep(0.5)
        print()

        action_signals_after = len([s for s in received_signals if s[0] == 'ActionInvoked'])

        print("6. Checking if ActionInvoked was emitted...")
        if action_signals_after > action_signals_before:
            print(f"   ✓ ActionInvoked signal was emitted")
            print()
            print("   🎉 SUCCESS: Action invoked successfully after popup expired!")
            print("   📝 However, if Discord isn't responding, it's because it already")
            print("      received NotificationClosed when the popup expired.")
        else:
            print(f"   ✗ No ActionInvoked signal received!")
            return False

        writer.close()
        await writer.wait_closed()

        print()
        print("=" * 70)
        print("ANALYSIS:")
        print("=" * 70)
        print()
        print("Signals received in order:")
        for i, signal in enumerate(received_signals, 1):
            if signal[0] == 'NotificationClosed':
                reasons = {1: 'Expired', 2: 'Dismissed by user', 3: 'Closed by call', 4: 'Undefined'}
                print(f"  {i}. {signal[0]}({signal[1]}, {signal[2]} = {reasons.get(signal[2], 'Unknown')})")
            else:
                print(f"  {i}. {signal[0]}({signal[1]}, '{signal[2]}')")
        print()

        # Check for the problematic pattern
        early_close = any(s for s in received_signals if s[0] == 'NotificationClosed' and s[2] == 1)
        late_action = any(s for s in received_signals if s[0] == 'ActionInvoked')

        if early_close and late_action:
            print("❌ BUG CONFIRMED:")
            print("  - NotificationClosed(reason=1, Expired) was emitted when popup expired")
            print("  - ActionInvoked was emitted later when user clicked in client")
            print("  - Applications like Discord stop listening after NotificationClosed")
            print("  - Therefore, they miss the ActionInvoked signal")
            print()
            print("FIX: Don't emit NotificationClosed when popup expires. Only emit it when:")
            print("  1. An action is invoked")
            print("  2. The notification is explicitly closed (CloseNotification D-Bus method)")
            return False
        else:
            print("✓ No issue detected (or bug already fixed)")
            return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(test_delayed_action())
    sys.exit(0 if success else 1)
