#!/usr/bin/env python3
"""Simple test to verify client can connect"""

import asyncio
import os
import sys

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from client import NotificationClient

async def test_connection():
    runtime_dir = os.environ.get('XDG_RUNTIME_DIR', '/tmp')
    socket_path = os.path.join(runtime_dir, 'waynotify', 'socket')
    
    print(f"Attempting to connect to: {socket_path}")
    
    client = NotificationClient(socket_path)
    
    if await client.connect():
        print("✓ Connected successfully!")
        
        # Get notifications
        notifications = await client.get_notifications()
        print(f"✓ Retrieved {len(notifications)} notifications")
        
        client.disconnect()
        print("✓ Disconnected cleanly")
        return True
    else:
        print("✗ Connection failed")
        return False

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_connection())
        sys.exit(0 if success else 1)
    finally:
        loop.close()
