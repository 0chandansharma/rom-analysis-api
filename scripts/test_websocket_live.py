#!/usr/bin/env python
"""
Simple WebSocket connection test with correct paths
"""
import asyncio
import websockets
import json
import base64
import numpy as np
import cv2

async def test_websocket():
    # Use the correct WebSocket path (no /api/v1 prefix)
    uri = "ws://localhost:8000/ws/test_session_001"
    
    print(f"Attempting to connect to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected successfully!")
            
            # Create a simple test frame
            frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
            # Draw a simple shape
            cv2.circle(frame, (320, 240), 50, (0, 0, 0), -1)
            
            # Encode to base64
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send a test message
            test_message = {
                "frame_base64": frame_base64,
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": False
            }
            
            print("Sending test message...")
            await websocket.send(json.dumps(test_message))
            
            # Wait for response
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"Received response:")
            print(f"  Status: {result.get('status', 'unknown')}")
            print(f"  Pose detected: {result.get('pose_detected', False)}")
            if result.get('pose_detected'):
                print(f"  ROM: {result.get('rom', {})}")
            elif 'error' in result:
                print(f"  Error: {result['error']}")
            else:
                print(f"  Message: {result.get('message', 'No message')}")
            
    except websockets.exceptions.WebSocketException as e:
        print(f"WebSocket error: {e}")
    except ConnectionRefusedError:
        print("Connection refused. Is the server running?")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def test_streaming():
    """Test the streaming endpoint"""
    uri = "ws://localhost:8000/ws/stream/test_stream_001"
    
    print(f"\nTesting streaming endpoint: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected to stream endpoint!")
            
            # Send configuration
            config = {
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": False
            }
            
            print("Sending configuration...")
            await websocket.send(json.dumps(config))
            
            # Wait for ready confirmation
            response = await websocket.recv()
            result = json.loads(response)
            print(f"Server response: {result}")
            
            if result.get("status") == "ready":
                print("Streaming 5 frames...")
                
                for i in range(5):
                    # Create frame with different poses
                    frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
                    # Draw circle at different positions to simulate movement
                    y_pos = 200 + i * 20
                    cv2.circle(frame, (320, y_pos), 50, (0, 0, 0), -1)
                    
                    # Encode to base64
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Send just the frame
                    print(f"Sending frame {i+1}...")
                    await websocket.send(frame_base64)
                    
                    # Get response
                    response = await websocket.recv()
                    result = json.loads(response)
                    
                    if result.get('status') == 'success':
                        print(f"  Frame {result.get('frame_number', i)}: "
                              f"ROM {result.get('rom', {}).get('current', 0):.1f}°")
                    else:
                        print(f"  Frame {i}: {result.get('error', 'Unknown error')}")
                    
                    # Small delay between frames
                    await asyncio.sleep(0.1)
                
                print("Streaming test completed!")
                
    except Exception as e:
        print(f"Streaming error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

async def main():
    print("WebSocket Test Suite")
    print("=" * 50)
    
    # Test single frame endpoint
    await test_websocket()
    
    # Test streaming endpoint
    await test_streaming()

if __name__ == "__main__":
    asyncio.run(main())