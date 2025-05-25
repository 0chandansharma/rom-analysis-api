import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement

class LowerBackRotation(Movement):
    """Lower back rotation analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_rotation"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["LShoulder", "RShoulder", "LHip", "RHip", "Neck", "Hip"]
    
    @property
    def primary_angle(self) -> str:
        return "trunk_rotation"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-45, 45)  # Negative for left rotation, positive for right
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate rotation angle based on shoulder and hip alignment"""
        angles = {}
        
        # Calculate rotation based on shoulder-hip alignment
        if all(k in keypoints for k in self.required_keypoints):
            # Shoulder line vector
            shoulder_vector = keypoints["RShoulder"] - keypoints["LShoulder"]
            shoulder_angle = np.degrees(np.arctan2(shoulder_vector[1], shoulder_vector[0]))
            
            # Hip line vector
            hip_vector = keypoints["RHip"] - keypoints["LHip"]
            hip_angle = np.degrees(np.arctan2(hip_vector[1], hip_vector[0]))
            
            # Rotation is difference between shoulder and hip angles
            rotation_angle = shoulder_angle - hip_angle
            
            # Normalize to [-180, 180]
            if rotation_angle > 180:
                rotation_angle -= 360
            elif rotation_angle < -180:
                rotation_angle += 360
            
            angles["trunk_rotation"] = rotation_angle
            angles["shoulder_line"] = shoulder_angle
            angles["hip_line"] = hip_angle
        
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate position for rotation measurement"""
        valid, message = super().validate_position(keypoints)
        if not valid:
            return valid, message
        
        # Check if person is reasonably upright
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_vector = keypoints["Neck"] - keypoints["Hip"]
            trunk_angle = np.degrees(np.arctan2(abs(trunk_vector[0]), -trunk_vector[1]))
            
            if trunk_angle > 30:
                return False, "Please stand more upright for rotation measurement"
        
        return True, "Position is correct"