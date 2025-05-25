#!/usr/bin/env python
"""
Debug script for single frame analysis
"""
import requests
import base64
import cv2
import json
import sys
import numpy as np

def create_test_frame():
    """Create a simple test frame with a stick figure"""
    # Create blank white image
    frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw a simple stick figure that resembles a person
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

def test_rom_api(image_path: str = None):
    """Test the ROM analysis API with detailed debugging"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/analyze/analyze"
    
    print("ROM Analysis API - Single Frame Test")
    print("=" * 50)
    
    # First, check if API is running
    try:
        health_response = requests.get("http://localhost:8000/api/v1/health/")
        print(f"✓ API is running: {health_response.json()}")
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API. Make sure the server is running.")
        print("  Run: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    except Exception as e:
        print(f"✗ Error checking API health: {e}")
        return
    
    # Check model readiness
    try:
        ready_response = requests.get("http://localhost:8000/api/v1/health/ready")
        ready_data = ready_response.json()
        print(f"✓ Model ready: {ready_data}")
        if not ready_data.get('model_loaded', False):
            print("✗ Warning: Model not loaded properly!")
    except Exception as e:
        print(f"✗ Error checking model readiness: {e}")
    
    print("\n" + "-" * 50 + "\n")
    
    # Create or load frame
    if image_path:
        print(f"Loading image from: {image_path}")
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"✗ Failed to load image: {image_path}")
            return
    else:
        print("Creating test frame with stick figure...")
        frame = create_test_frame()
        # Save test frame for debugging
        cv2.imwrite("test_frame.jpg", frame)
        print("✓ Test frame saved as 'test_frame.jpg'")
    
    # Encode frame to base64
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    print(f"✓ Frame encoded: {len(frame_base64)} characters")
    
    # Prepare request
    request_data = {
        "frame_base64": frame_base64,
        "session_id": "test_session_001",
        "body_part": "lower_back",
        "movement_type": "flexion",
        "include_keypoints": True,
        "include_visualization": False
    }
    
    print("\nSending request to API...")
    print(f"  Body part: {request_data['body_part']}")
    print(f"  Movement: {request_data['movement_type']}")
    
    # Send request with detailed error handling
    try:
        response = requests.post(url, json=request_data)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Check if response is JSON
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            print(f"✗ Unexpected content type: {content_type}")
            print(f"Response text: {response.text[:500]}...")
            return
        
        # Try to parse JSON
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"\nRaw JSON response: {result}")
                
                if result is None:
                    print("✗ API returned None/null")
                    return
                
                print("\n✓ Success! Results:")
                print(f"  Timestamp: {result.get('timestamp', 'N/A')}")
                print(f"  Frame ID: {result.get('frame_id', 'N/A')}")
                print(f"  Pose Detected: {result.get('pose_detected', False)}")
                
                if result.get('pose_detected'):
                    print(f"  Pose Confidence: {result.get('pose_confidence', 0):.2%}")
                    print(f"  Angles Detected: {json.dumps(result.get('angles', {}), indent=4)}")
                    print(f"  ROM Data: {json.dumps(result.get('rom', {}), indent=4)}")
                    print(f"  Validation: {result.get('validation', {}).get('message', 'N/A')}")
                    print(f"  Guidance: {result.get('guidance', {}).get('instruction', 'N/A')}")
                    
                    if 'keypoints' in result:
                        print(f"  Keypoints detected: {len(result['keypoints'])}")
                else:
                    print(f"  Message: {result.get('message', 'No message')}")
                    
            except json.JSONDecodeError as e:
                print(f"✗ Failed to parse JSON response: {e}")
                print(f"Response text: {response.text[:500]}...")
        else:
            print(f"✗ Error {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ Error: Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if image path provided
    # image_path = sys.argv[1] if len(sys.argv) > 1 else None
    image_path = '/Users/chandansharma/Desktop/workspace/deecogs-workspace/chandanrnd/rom-analysis-api/scripts/me1.jpg'
    # Run test
    test_rom_api(image_path)