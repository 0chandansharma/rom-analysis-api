# test_minimal_ws.py
import asyncio
import websockets
import json
import base64
import numpy as np
import cv2

async def test():
    # Create a simple test image with a person-like shape
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Draw a simple stick figure
    # Head
    cv2.circle(img, (320, 100), 30, (0, 0, 0), -1)
    # Body
    cv2.line(img, (320, 130), (320, 250), (0, 0, 0), 5)
    # Arms
    cv2.line(img, (320, 150), (250, 200), (0, 0, 0), 5)
    cv2.line(img, (320, 150), (390, 200), (0, 0, 0), 5)
    # Legs
    cv2.line(img, (320, 250), (280, 350), (0, 0, 0), 5)
    cv2.line(img, (320, 250), (360, 350), (0, 0, 0), 5)
    
    # Save for inspection
    cv2.imwrite("/Users/chandansharma/Desktop/workspace/deecogs-workspace/chandanrnd/rom-analysis-api/scripts/me1.jpg", img)
    
    # Encode
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    async with websockets.connect("ws://localhost:8000/ws/test_minimal") as ws:
        await ws.send(json.dumps({
            "frame_base64": img_base64,
            "body_part": "lower_back",
            "movement_type": "flexion",
            "include_keypoints": True
        }))
        
        response = await ws.recv()
        print(json.dumps(json.loads(response), indent=2))

asyncio.run(test())