#!/usr/bin/env python3
"""
Simple Python WebSocket test for ROM Analysis API
Can use webcam or test images
"""

import asyncio
import websockets
import json
import base64
import cv2
import numpy as np
import time
from datetime import datetime

class ROMWebSocketTester:
    def __init__(self, base_url="ws://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session_id = f"python_test_{int(time.time())}"
        
    def create_test_frame(self, angle=0):
        """Create a simple test frame with a stick figure at different angles"""
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        
        # Center point
        cx, cy = 320, 240
        
        # Draw stick figure with varying angle for flexion simulation
        # Head
        head_y = cy - 140 + int(angle * 0.5)
        cv2.circle(frame, (cx, head_y), 30, (0, 0, 0), -1)
        
        # Spine (bent for flexion)
        spine_points = []
        for i in range(5):
            t = i / 4.0
            x = cx + int(angle * t * 0.3)
            y = head_y + 30 + int(110 * t)
            spine_points.append((x, y))
        
        # Draw spine
        for i in range(len(spine_points) - 1):
            cv2.line(frame, spine_points[i], spine_points[i+1], (0, 0, 0), 5)
        
        # Arms
        shoulder_point = spine_points[1]
        cv2.line(frame, shoulder_point, (shoulder_point[0] - 70, shoulder_point[1] + 50), (0, 0, 0), 5)
        cv2.line(frame, shoulder_point, (shoulder_point[0] + 70, shoulder_point[1] + 50), (0, 0, 0), 5)
        
        # Legs
        hip_point = spine_points[-1]
        cv2.line(frame, hip_point, (hip_point[0] - 40, hip_point[1] + 100), (0, 0, 0), 5)
        cv2.line(frame, hip_point, (hip_point[0] + 40, hip_point[1] + 100), (0, 0, 0), 5)
        
        # Add angle text
        cv2.putText(frame, f"Simulated angle: {angle}°", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return frame
    
    async def test_single_frame_analysis(self):
        """Test single frame WebSocket endpoint"""
        print("\n=== Testing Single Frame Analysis ===")
        
        uri = f"{self.base_url}/ws/{self.session_id}"
        
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            # Create test frame
            frame = self.create_test_frame(30)
            _, buffer = cv2.imencode('.jpg', frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send analysis request
            request = {
                "frame_base64": frame_base64,
                "body_part": "lower_back",
                "movement_type": "flexion",
                "include_keypoints": True
            }
            
            print("Sending frame for analysis...")
            await websocket.send(json.dumps(request))
            
            # Receive response
            response = await websocket.recv()
            result = json.loads(response)
            
            print("\nAnalysis Result:")
            print(f"  Pose Detected: {result.get('pose_detected', False)}")
            if result.get('pose_detected'):
                print(f"  Confidence: {result.get('pose_confidence', 0):.2%}")
                print(f"  Angles: {json.dumps(result.get('angles', {}), indent=4)}")
                print(f"  ROM: {json.dumps(result.get('rom', {}), indent=4)}")
                print(f"  Validation: {result.get('validation', {}).get('message', '')}")
            else:
                print(f"  Message: {result.get('message', 'No message')}")
    
    async def test_streaming_analysis(self, duration=5, fps=10):
        """Test streaming WebSocket endpoint"""
        print(f"\n=== Testing Streaming Analysis ({duration}s at {fps} FPS) ===")
        
        uri = f"{self.base_url}/ws/stream/{self.session_id}_stream"
        
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
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
                # Simulate movement over time
                start_time = time.time()
                frame_count = 0
                max_angle = 0
                min_angle = 90
                
                print("\nStreaming frames...")
                print("Time | Angle | ROM Current | ROM Range")
                print("-" * 50)
                
                while time.time() - start_time < duration:
                    # Create frame with varying angle (simulate bending motion)
                    elapsed = time.time() - start_time
                    angle = int(45 * np.sin(elapsed * 0.5) + 45)  # Oscillate between 0 and 90
                    
                    frame = self.create_test_frame(angle)
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Send frame
                    await websocket.send(frame_base64)
                    
                    # Receive analysis result
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        result = json.loads(response)
                        
                        if result.get('rom'):
                            rom = result['rom']
                            current = rom.get('current', 0)
                            rom_range = rom.get('range', 0)
                            
                            print(f"{elapsed:4.1f}s | {angle:3d}° | {current:6.1f}° | {rom_range:5.1f}°")
                            
                            max_angle = max(max_angle, current)
                            min_angle = min(min_angle, current)
                        
                        frame_count += 1
                    except asyncio.TimeoutError:
                        print(f"Timeout waiting for response at {elapsed:.1f}s")
                    
                    # Wait to maintain FPS
                    await asyncio.sleep(1.0 / fps)
                
                print(f"\nStreaming completed!")
                print(f"  Frames sent: {frame_count}")
                print(f"  Detected ROM range: {min_angle:.1f}° to {max_angle:.1f}°")
    
    async def test_webcam_streaming(self, duration=10):
        """Test with real webcam input"""
        print(f"\n=== Testing Webcam Streaming ({duration}s) ===")
        
        # Open webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open webcam")
            return
        
        uri = f"{self.base_url}/ws/stream/{self.session_id}_webcam"
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to {uri}")
                
                # Send configuration
                config = {
                    "body_part": "lower_back",
                    "movement_type": "flexion",
                    "include_keypoints": False
                }
                
                await websocket.send(json.dumps(config))
                
                # Wait for ready
                response = await websocket.recv()
                result = json.loads(response)
                
                if result.get("status") == "ready":
                    print("Streaming webcam frames... Press Ctrl+C to stop")
                    
                    start_time = time.time()
                    frame_count = 0
                    
                    while time.time() - start_time < duration:
                        ret, frame = cap.read()
                        if not ret:
                            print("Failed to read frame from webcam")
                            break
                        
                        # Resize frame if too large
                        height, width = frame.shape[:2]
                        if width > 640:
                            scale = 640 / width
                            new_width = int(width * scale)
                            new_height = int(height * scale)
                            frame = cv2.resize(frame, (new_width, new_height))
                        
                        # Convert to base64
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_base64 = base64.b64encode(buffer).decode('utf-8')
                        
                        # Send frame
                        await websocket.send(frame_base64)
                        
                        # Receive result
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                            result = json.loads(response)
                            
                            if result.get('pose_detected') and result.get('rom'):
                                rom = result['rom']
                                print(f"Frame {frame_count}: ROM {rom['current']:.1f}° "
                                      f"(range: {rom['min']:.1f}° - {rom['max']:.1f}°)")
                            elif not result.get('pose_detected'):
                                print(f"Frame {frame_count}: No pose detected")
                            
                            frame_count += 1
                        except asyncio.TimeoutError:
                            pass
                        
                        # Small delay
                        await asyncio.sleep(0.1)
                    
                    print(f"\nWebcam streaming completed! Processed {frame_count} frames")
                    
        finally:
            cap.release()

async def main():
    """Run all tests"""
    tester = ROMWebSocketTester()
    
    try:
        # Test single frame
        await tester.test_single_frame_analysis()
        
        # Test streaming with synthetic data
        await tester.test_streaming_analysis(duration=5, fps=10)
        
        # Optional: Test with webcam
        response = input("\nTest with webcam? (y/n): ")
        if response.lower() == 'y':
            await tester.test_webcam_streaming(duration=10)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("ROM Analysis WebSocket Test Suite")
    print("=" * 50)
    asyncio.run(main())