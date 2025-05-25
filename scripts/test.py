#!/usr/bin/env python
"""
Test script for ROM Analysis API
Includes REST and WebSocket tests
"""
import requests
import base64
import cv2
import json
import sys
import asyncio
import websockets
import numpy as np

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
WS_BASE_URL = "ws://localhost:8000/api/v1/ws"

def create_test_frame():
    """Create a simple test frame with a person-like shape"""
    # Create blank image
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw a simple stick figure
    # Head
    cv2.circle(frame, (320, 100), 30, (0, 0, 0), -1)
    
    # Body
    cv2.line(frame, (320, 130), (320, 250), (0, 0, 0), 5)
    
    # Arms
    cv2.line(frame, (320, 150), (250, 200), (0, 0, 0), 5)  # Left arm
    cv2.line(frame, (320, 150), (390, 200), (0, 0, 0), 5)  # Right arm
    
    # Legs
    cv2.line(frame, (320, 250), (280, 350), (0, 0, 0), 5)  # Left leg
    cv2.line(frame, (320, 250), (360, 350), (0, 0, 0), 5)  # Right leg
    
    return frame

def test_health_check():
    """Test health check endpoint"""
    print("\n=== Testing Health Check ===")
    
    response = requests.get(f"{API_BASE_URL}/health/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Test readiness
    response = requests.get(f"{API_BASE_URL}/health/ready")
    print(f"\nReadiness Check: {json.dumps(response.json(), indent=2)}")

def test_rom_analysis(image_path: str = None):
    """Test the ROM analysis API"""
    print("\n=== Testing ROM Analysis ===")
    
    # Create or load frame
    if image_path:
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Failed to load image: {image_path}")
            return
    else:
        print("Creating test frame...")
        frame = create_test_frame()
    
    # Encode frame to base64
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Test different movements
    test_cases = [
        {
            "body_part": "lower_back",
            "movement_type": "flexion",
            "description": "Lower Back Flexion"
        },
        {
            "body_part": "lower_back",
            "movement_type": "extension",
            "description": "Lower Back Extension"
        },
        {
            "body_part": "lower_back",
            "movement_type": "lateral_flexion",
            "description": "Lower Back Lateral Flexion"
        },
        {
            "body_part": "lower_back",
            "movement_type": "rotation",
            "description": "Lower Back Rotation"
        }
    ]
    
    session_id = "test_session_001"
    
    for test_case in test_cases:
        print(f"\n--- Testing {test_case['description']} ---")
        
        # Prepare request
        request_data = {
            "frame_base64": frame_base64,
            "session_id": session_id,
            "body_part": test_case["body_part"],
            "movement_type": test_case["movement_type"],
            "include_keypoints": True,
            "include_visualization": False
        }
        
        # Send request
        try:
            response = requests.post(
                f"{API_BASE_URL}/analyze/analyze",
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Success!")
                print(f"  Pose Detected: {result['pose_detected']}")
                print(f"  Confidence: {result['pose_confidence']:.2%}")
                if result['pose_detected']:
                    print(f"  Angles: {json.dumps(result['angles'], indent=4)}")
                    print(f"  ROM: {json.dumps(result['rom'], indent=4)}")
                    print(f"  Validation: {result['validation']['message']}")
                else:
                    print(f"  Message: {result['message']}")
            else:
                print(f"✗ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("✗ Error: Could not connect to API. Make sure the server is running.")
        except Exception as e:
            print(f"✗ Error: {e}")

def test_session_management():
    """Test session management endpoints"""
    print("\n=== Testing Session Management ===")
    
    session_id = "test_session_001"
    
    # Get session data
    print(f"\nGetting session data for {session_id}...")
    response = requests.get(f"{API_BASE_URL}/sessions/session/{session_id}")
    
    if response.status_code == 200:
        session_data = response.json()
        print(f"Session Data: {json.dumps(session_data, indent=2)}")
    else:
        print(f"No session data found (status: {response.status_code})")
    
    # Clear session
    print(f"\nClearing session {session_id}...")
    response = requests.delete(f"{API_BASE_URL}/sessions/session/{session_id}")
    print(f"Response: {response.json()}")

async def test_websocket():
    """Test WebSocket connection for real-time analysis"""
    print("\n=== Testing WebSocket Connection ===")
    
    session_id = "test_ws_session"
    uri = f"{WS_BASE_URL}/{session_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket at {uri}")
            
            # Create test frame
            frame = create_test_frame()
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send analysis request
            request_data = {
                "frame_base64": frame_base64,
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": True
            }
            
            print("Sending frame for analysis...")
            await websocket.send(json.dumps(request_data))
            
            # Receive response
            response = await websocket.recv()
            result = json.loads(response)
            
            print(f"Received response:")
            print(f"  Pose Detected: {result.get('pose_detected', False)}")
            if result.get('pose_detected'):
                print(f"  Angles: {result.get('angles', {})}")
                print(f"  ROM: {result.get('rom', {})}")
            else:
                print(f"  Message: {result.get('message', 'No message')}")
            
            print("WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"WebSocket test failed: {e}")

async def test_websocket_stream():
    """Test WebSocket streaming for continuous analysis"""
    print("\n=== Testing WebSocket Streaming ===")
    
    session_id = "test_stream_session"
    uri = f"{WS_BASE_URL}/stream/{session_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to WebSocket stream at {uri}")
            
            # Send configuration
            config = {
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": False
            }
            
            print("Sending configuration...")
            await websocket.send(json.dumps(config))
            
            # Receive ready confirmation
            response = await websocket.recv()
            result = json.loads(response)
            print(f"Server response: {result}")
            
            if result.get("status") == "ready":
                # Send multiple frames
                print("Sending frames...")
                for i in range(3):
                    frame = create_test_frame()
                    # Simulate movement by shifting the figure
                    frame = np.roll(frame, i * 10, axis=1)
                    
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    await websocket.send(frame_base64)
                    
                    # Receive analysis result
                    response = await websocket.recv()
                    result = json.loads(response)
                    print(f"Frame {i}: ROM = {result.get('rom', {}).get('current', 0)}°")
                
                print("Streaming test completed!")
            
    except Exception as e:
        print(f"Streaming test failed: {e}")

def main():
    """Run all tests"""
    print("ROM Analysis API Test Suite")
    print("=" * 50)
    
    # Check if custom image provided
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Run tests
    test_health_check()
    test_rom_analysis(image_path)
    test_session_management()
    
    # Run async tests
    print("\nRunning WebSocket tests...")
    asyncio.run(test_websocket())
    asyncio.run(test_websocket_stream())
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    main()