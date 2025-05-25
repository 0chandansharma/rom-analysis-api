#!/usr/bin/env python
"""
Minimal test to check what's happening
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import numpy as np
import cv2
import base64

async def test_components():
    """Test each component individually"""
    
    print("Testing individual components...")
    
    # 1. Test image processor
    print("\n1. Testing ImageProcessor...")
    try:
        from app.services.image_processor import ImageProcessor
        processor = ImageProcessor()
        
        # Create test image
        test_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
        _, buffer = cv2.imencode('.jpg', test_img)
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        # Decode
        decoded = processor.decode_base64(base64_str)
        print(f"   ✓ Image decoded: shape={decoded.shape}")
    except Exception as e:
        print(f"   ✗ ImageProcessor failed: {e}")
        return
    
    # 2. Test pose processor
    print("\n2. Testing PoseProcessor...")
    try:
        from app.core.pose.processor import PoseProcessor
        pose_proc = PoseProcessor()
        
        # Create better test image (larger with stick figure)
        test_img = np.ones((480, 640, 3), dtype=np.uint8) * 255
        # Draw stick figure
        cv2.circle(test_img, (320, 100), 30, (0, 0, 0), -1)  # Head
        cv2.line(test_img, (320, 130), (320, 250), (0, 0, 0), 5)  # Body
        cv2.line(test_img, (320, 150), (250, 200), (0, 0, 0), 5)  # Left arm
        cv2.line(test_img, (320, 150), (390, 200), (0, 0, 0), 5)  # Right arm
        cv2.line(test_img, (320, 250), (280, 350), (0, 0, 0), 5)  # Left leg
        cv2.line(test_img, (320, 250), (360, 350), (0, 0, 0), 5)  # Right leg
        
        keypoints, confidence = pose_proc.process_frame(test_img)
        print(f"   ✓ Pose detected: {len(keypoints)} keypoints, confidence={confidence:.3f}")
        if len(keypoints) > 0:
            print(f"   Keypoints: {list(keypoints.keys())[:5]}...")
    except Exception as e:
        print(f"   ✗ PoseProcessor failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 3. Test frame analyzer
    print("\n3. Testing FrameAnalyzer...")
    try:
        from app.services.session_manager import SessionManager
        from app.storage.memory import InMemoryStorage
        from app.services.frame_analyzer import FrameAnalyzer
        
        storage = InMemoryStorage()
        session_mgr = SessionManager(storage)
        analyzer = FrameAnalyzer(session_mgr)
        
        # Encode test image
        _, buffer = cv2.imencode('.jpg', test_img)
        base64_str = base64.b64encode(buffer).decode('utf-8')
        
        # Analyze
        result = await analyzer.analyze(
            frame_base64=base64_str,
            session_id="test_minimal",
            body_part="lower_back",
            movement_type="flexion",
            include_keypoints=False
        )
        
        print(f"   ✓ Analysis complete:")
        print(f"     - Pose detected: {result.get('pose_detected', False)}")
        print(f"     - Angles: {result.get('angles', {})}")
        print(f"     - ROM: {result.get('rom', {})}")
        
    except Exception as e:
        print(f"   ✗ FrameAnalyzer failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_components())