#!/usr/bin/env python3
"""
Simple Socket.IO Connection Test - Stay Connected Longer
"""

import socketio
import time
import threading

# Configuration
SOCKET_URL = "https://pilot-ready-deploy.preview.emergentagent.com"
SOCKET_PATH = "/api/socket.io"

def test_long_connection():
    """Test Socket.IO connection for longer period"""
    print("=== Long Connection Socket.IO Test ===")
    
    # Set up Socket.IO client with more verbose logging
    sio = socketio.Client(logger=True, engineio_logger=True)
    events_received = []
    
    @sio.event
    def connect():
        print("✅ Socket.IO connected")
        events_received.append("connected")
    
    @sio.event
    def disconnect():
        print("Socket.IO disconnected")
        events_received.append("disconnected")
    
    @sio.event
    def connect_error(data):
        print(f"❌ Connection error: {data}")
        events_received.append("connect_error")
    
    # Catch all events
    @sio.event
    def catch_all(event, *args):
        print(f"📨 Received event '{event}': {args}")
        events_received.append(event)
    
    try:
        # Connect to socket
        print("Connecting to Socket.IO...")
        sio.connect(SOCKET_URL, socketio_path=SOCKET_PATH, wait_timeout=10)
        
        if not sio.connected:
            print("❌ Failed to connect")
            return False
        
        print("✅ Connected successfully")
        print(f"Transport: {sio.transport()}")
        
        # Stay connected for 15 seconds to see what events come through
        print("Staying connected for 15 seconds to monitor events...")
        time.sleep(15)
        
        print(f"Total events received: {len(events_received)}")
        print(f"Events: {events_received}")
        
        # Disconnect
        sio.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_long_connection()
    print(f"\nLong connection test {'PASSED' if success else 'FAILED'}")