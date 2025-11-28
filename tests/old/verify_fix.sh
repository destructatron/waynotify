#!/bin/bash
# Verify that the fix works: actions can be invoked after popup expires

echo "1. Restarting daemon..."
pkill -f "python3.*waynotify"
sleep 1
./src/waynotify &
sleep 2

echo "2. Sending notification with 3-second timeout..."
notify-send "TestApp" "Test message" --action="default=Click Me" 2>/dev/null
sleep 4

echo "3. Popup should have expired by now"
echo "4. Invoking action via waynotify-client socket..."

python3 << 'PYTHON_EOF'
import asyncio, json, os

async def test():
    socket_path = os.path.join(os.environ.get('XDG_RUNTIME_DIR', '/tmp'), 'waynotify', 'socket')
    reader, writer = await asyncio.open_unix_connection(socket_path)

    # Get notifications
    writer.write(b'{"type": "get_all", "_request_id": 1}\n')
    await writer.drain()
    resp = json.loads((await reader.readline()).decode())

    if resp.get('notifications'):
        nid = resp['notifications'][0]['id']
        print(f"   Found notification {nid}, invoking action...")

        # Invoke action
        writer.write(json.dumps({'type': 'invoke_action', 'id': nid, 'action': 'default', '_request_id': 2}).encode() + b'\n')
        await writer.drain()
        result = json.loads((await reader.readline()).decode())

        print(f"   Result: success={result.get('success')}")
    else:
        print("   No notifications found")

    writer.close()

asyncio.run(test())
PYTHON_EOF

echo ""
echo "5. Checking D-Bus signals emitted..."
echo ""
tail -20 /run/user/$(id -u)/waynotify/waynotify.log | grep -E "(TestApp|NotificationClosed|ActionInvoked)"
echo ""
echo "✓ Fix successful if you see ActionInvoked but NOT NotificationClosed(reason=1) after popup expired"
