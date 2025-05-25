#!/usr/bin/env python
import requests
import base64
import cv2
import json
import sys

def test_rom_api(image_path: str = None):
    """Test the ROM analysis API"""
    
    # API endpoint
    url = "http://localhost:8000/api/v1/analyze/analyze"
    
    # Capture frame from webcam if no image provided
    if not image_path:
        print("Capturing frame from webcam...")
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("Failed to capture frame from webcam")
            return
    else:
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Failed to load image: {image_path}")
            return
    
    # Encode frame to base64
    _, buffer = cv2.imencode('.jpg', frame)
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    
    # Prepare request
    request_data = {
        "frame_base64": frame_base64,
        "session_id": "test_session_001",
        "body_part": "lower_back",
        "movement_type": "flexion",
        "include_keypoints": True,
        "include_visualization": False
    }
    
    # Send request
    print("Sending request to API...")
    try:
        response = requests.post(url, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            print("\nSuccess! Results:")
            print(f"Timestamp: {result['timestamp']}")
            print(f"Frame ID: {result['frame_id']}")
            print(f"Pose Confidence: {result['pose_confidence']:.2%}")
            print(f"Angles: {json.dumps(result['angles'], indent=2)}")
            print(f"ROM Data: {json.dumps(result['rom'], indent=2)}")
        else:
            print(f"\nError {response.status_code}: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Make sure the server is running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_rom_api(image_path)