#!/usr/bin/env python
"""
Simple WebSocket connection test
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/api/v1/ws/test_simple"
    
    print(f"Attempting to connect to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            
            # Send a test message
            test_message = {
                "frame_base64": "test",
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": False
            }
            
            print("Sending test message...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            print(f"Received: {response}")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}")
    except ConnectionRefusedError:
        print("Connection refused. Is the server running?")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("Simple WebSocket Test")
    print("=" * 50)
    asyncio.run(test_websocket())