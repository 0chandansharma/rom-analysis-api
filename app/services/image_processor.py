import base64
import cv2
import numpy as np
from typing import Dict, Optional
from io import BytesIO

class ImageProcessor:
    """Handle image encoding/decoding and visualization"""
    
    @staticmethod
    def decode_base64(base64_string: str) -> np.ndarray:
        """Decode base64 string to numpy array"""
        # Remove data URL prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        # Decode base64
        img_bytes = base64.b64decode(base64_string)
        
        # Convert to numpy array
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image")
        
        return img
    
    @staticmethod
    def encode_base64(image: np.ndarray, format: str = ".jpg") -> str:
        """Encode numpy array to base64 string"""
        # Encode image
        success, buffer = cv2.imencode(format, image)
        if not success:
            raise ValueError("Failed to encode image")
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        return img_base64
    
    def draw_visualization(
        self,
        frame: np.ndarray,
        keypoints: Dict[str, np.ndarray],
        angles: Dict[str, float],
        rom_data: Dict[str, float]
    ) -> np.ndarray:
        """Draw pose skeleton and angle information on frame"""
        viz_frame = frame.copy()
        
        # Draw skeleton
        self._draw_skeleton(viz_frame, keypoints)
        
        # Draw angle values
        self._draw_angle_info(viz_frame, angles, rom_data)
        
        return viz_frame
    
    def _draw_skeleton(self, frame: np.ndarray, keypoints: Dict[str, np.ndarray]):
        """Draw skeleton connections"""
        # Define connections
        connections = [
            ("LShoulder", "RShoulder"),
            ("LShoulder", "LElbow"),
            ("LElbow", "LWrist"),
            ("RShoulder", "RElbow"),
            ("RElbow", "RWrist"),
            ("LShoulder", "LHip"),
            ("RShoulder", "RHip"),
            ("LHip", "RHip"),
            ("LHip", "LKnee"),
            ("LKnee", "LAnkle"),
            ("RHip", "RKnee"),
            ("RKnee", "RAnkle"),
            ("Neck", "Hip"),
            ("Neck", "Head") if "Head" in keypoints else ("Neck", "Nose")
        ]
        
        # Draw connections
        for start, end in connections:
            if start in keypoints and end in keypoints:
                pt1 = tuple(keypoints[start].astype(int))
                pt2 = tuple(keypoints[end].astype(int))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
        
        # Draw keypoints
        for name, point in keypoints.items():
            cv2.circle(frame, tuple(point.astype(int)), 5, (0, 0, 255), -1)
    
    def _draw_angle_info(
        self, 
        frame: np.ndarray, 
        angles: Dict[str, float], 
        rom_data: Dict[str, float]
    ):
        """Draw angle and ROM information"""
        # Draw text background
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        
        # Draw angle values
        y_pos = 30
        for angle_name, angle_value in angles.items():
            text = f"{angle_name}: {angle_value:.1f}°"
            cv2.putText(
                frame, text, (20, y_pos),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
            )
            y_pos += 25
        
        # Draw ROM data
        y_pos += 10
        cv2.putText(
            frame, f"ROM: {rom_data['range']:.1f}° ({rom_data['min']:.1f}° - {rom_data['max']:.1f}°)",
            (20, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2
        )