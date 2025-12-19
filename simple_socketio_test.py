#!/usr/bin/env python3
"""
Simple Socket.IO Connection Test

Tests basic Socket.IO connectivity to verify the server is working.
"""

import socketio
import time
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fix-roster-sync.preview.emergentagent.com')
SOCKET_URL = f"{BACKEND_URL}/api/socket.io"

def test_socketio_connection():
    """Test basic Socket.IO connection"""
    print(f"🔌 Testing Socket.IO connection to: {SOCKET_URL}")
    
    # Create synchronous client
    sio = socketio.Client()
    
    @sio.event
    def connect():
        print("✅ Socket.IO connected successfully!")
        
    @sio.event
    def disconnect():
        print("🔌 Socket.IO disconnected")
        
    @sio.event
    def connect_error(data):
        print(f"❌ Socket.IO connection error: {data}")
        
    try:
        # Try to connect
        sio.connect(SOCKET_URL, transports=['polling', 'websocket'])
        
        # Wait a moment
        time.sleep(2)
        
        # Test emitting an event
        sio.emit('test_event', {'message': 'Hello from test client'})
        
        # Wait a bit more
        time.sleep(1)
        
        # Disconnect
        sio.disconnect()
        
        return True
        
    except Exception as e:
        print(f"❌ Socket.IO test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_socketio_connection()
    if success:
        print("🎯 Socket.IO basic connectivity: WORKING")
    else:
        print("🚨 Socket.IO basic connectivity: FAILED")