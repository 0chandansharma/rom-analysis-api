# scripts/test_with_image.py
import requests
import base64
import cv2

# Use a clear image of a person
img = cv2.imread("/Users/chandansharma/Desktop/workspace/deecogs-workspace/chandanrnd/rom-analysis-api/scripts/me1.jpg")  # Use a clear photo of a person
_, buffer = cv2.imencode('.jpg', img)
img_base64 = base64.b64encode(buffer).decode('utf-8')

response = requests.post(
    "http://localhost:8000/api/v1/analyze/analyze",
    json={
        "frame_base64": img_base64,
        "session_id": "debug_test",
        "body_part": "lower_back",
        "movement_type": "flexion",
        "include_keypoints": True
    }
)

print(response.json())