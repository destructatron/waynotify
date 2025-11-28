#!/usr/bin/env python3
"""
Test to check if request_id=0 is handled correctly
This simulates the exact client behavior with the first request
"""
import asyncio
import json
import os
import sys

async def test_request_id_zero():
    """Test that request_id=0 (first request) works correctly"""
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')

    if not os.path.exists(socket_path):
        print(f"Error: Socket not found at {socket_path}")
        return False

    try:
        print("1. Connecting to daemon...")
        reader, writer = await asyncio.open_unix_connection(socket_path)
        print("   ✓ Connected")
        print()

        # Simulate the client's _message_reader and send_message pattern
        pending_responses = {}
        next_request_id = [0]  # Using list to allow modification in nested function
        running = [True]
        received_response = [None]

        async def message_reader():
            """Simulates client's _message_reader()"""
            while running[0]:
                try:
                    data = await reader.readline()
                    if not data:
                        break

                    message = json.loads(data.decode().strip())
                    print(f"   [READER] Received message: type={message.get('type')}, _request_id={message.get('_request_id')}")

                    # Check if this is a response to a pending request
                    request_id = message.get('_request_id')
                    print(f"   [READER] Checking: request_id={request_id}, is not None? {request_id is not None}")
                    print(f"   [READER] Pending responses dict: {list(pending_responses.keys())}")

                    if request_id is not None and request_id in pending_responses:
                        print(f"   [READER] ✓ Match found! Resolving future for request_id={request_id}")
                        future = pending_responses.pop(request_id)
                        future.set_result(message)
                        received_response[0] = message
                    else:
                        print(f"   [READER] ✗ No match! request_id={request_id} not in pending_responses")
                        if request_id is not None:
                            print(f"   [READER] request_id is not None, but not in dict")
                        if request_id == 0:
                            print(f"   [READER] request_id is 0 - checking truthiness: bool(0)={bool(0)}")

                except json.JSONDecodeError as e:
                    print(f"   [READER] JSON decode error: {e}")
                    continue
                except Exception as e:
                    print(f"   [READER] Error: {e}")
                    break

        # Start message reader
        print("2. Starting message reader task...")
        reader_task = asyncio.create_task(message_reader())
        await asyncio.sleep(0.1)  # Let reader start
        print("   ✓ Reader started")
        print()

        # Send request with ID = 0 (like the first client request)
        print("3. Sending get_all request with _request_id=0...")
        request_id = next_request_id[0]
        next_request_id[0] += 1

        print(f"   request_id = {request_id}")
        print(f"   type(request_id) = {type(request_id)}")
        print(f"   request_id is not None = {request_id is not None}")
        print(f"   bool(request_id) = {bool(request_id)}")

        message = {'type': 'get_all', '_request_id': request_id}

        # Create future for response
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        pending_responses[request_id] = future
        print(f"   Stored future in pending_responses[{request_id}]")
        print(f"   pending_responses keys: {list(pending_responses.keys())}")

        # Send message
        message_str = json.dumps(message) + '\n'
        writer.write(message_str.encode())
        await writer.drain()
        print(f"   ✓ Sent: {message}")
        print()

        # Wait for response
        print("4. Waiting for response (5 second timeout)...")
        try:
            response = await asyncio.wait_for(future, timeout=5.0)
            print(f"   ✓ Got response!")
            print(f"   Response type: {response.get('type')}")

            if response.get('type') == 'notification_list':
                notifications = response.get('notifications', [])
                print(f"   Notifications in list: {len(notifications)}")
                for n in notifications:
                    print(f"     - ID {n['id']}: {n['summary']}")
                print()

                if len(notifications) > 0:
                    print("✓ SUCCESS: Received notification list with request_id=0")
                    return True
                else:
                    print("✗ FAIL: Got empty notification list")
                    return False
            else:
                print(f"✗ FAIL: Unexpected response type: {response.get('type')}")
                return False

        except asyncio.TimeoutError:
            print("   ✗ TIMEOUT: No response received!")
            print(f"   pending_responses after timeout: {list(pending_responses.keys())}")
            print(f"   received_response: {received_response[0]}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        running[0] = False
        try:
            reader_task.cancel()
            await asyncio.sleep(0.1)
        except:
            pass
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

if __name__ == '__main__':
    success = asyncio.run(test_request_id_zero())
    sys.exit(0 if success else 1)
