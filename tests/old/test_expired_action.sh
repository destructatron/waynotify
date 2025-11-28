#!/bin/bash
# Test that action invocation fails after notification expires

echo "Killing existing daemon..."
pkill -f "python3.*waynotify"
sleep 2

echo "Starting daemon with debug logging..."
./src/waynotify > /tmp/waynotify_test.log 2>&1 &
DAEMON_PID=$!
sleep 3

echo "Running test..."
python3 << 'EOF'
import asyncio, json, os, sys
from dasbus.connection import SessionMessageBus

async def test():
    try:
        bus = SessionMessageBus()
        notify = bus.get_proxy('org.freedesktop.Notifications', '/org/freedesktop/Notifications')

        print('1. Sending notification with 2-second timeout...')
        notif_id = notify.Notify('TestApp', 0, 'dialog-information', 'Test', 'Message', ['action1', 'Click Me'], {}, 2000)
        print(f'   Notification {notif_id} sent')

        print('2. Waiting 3 seconds for popup to expire...')
        await asyncio.sleep(3)

        print('3. Invoking action via socket...')
        socket_path = os.path.join(os.environ.get('XDG_RUNTIME_DIR', '/tmp'), 'waynotify', 'socket')
        reader, writer = await asyncio.open_unix_connection(socket_path)

        request = {'type': 'invoke_action', 'id': notif_id, 'action': 'action1', '_request_id': 1}
        writer.write((json.dumps(request) + '\n').encode())
        await writer.drain()

        response = await asyncio.wait_for(reader.readline(), timeout=2.0)
        result = json.loads(response.decode().strip())
        print(f'   Response: success={result.get("success")}')

        writer.close()
        return notif_id
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return None

notif_id = asyncio.run(test())
print(f'\nNotification ID tested: {notif_id}')
EOF

echo ""
echo "=== Daemon logs ==="
cat /tmp/waynotify_test.log | grep -E "(DEBUG|TestApp|notification)"

kill $DAEMON_PID 2>/dev/null
