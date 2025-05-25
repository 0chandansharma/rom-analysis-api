import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_angle_between_points, compute_angle, add_virtual_keypoints

class ShoulderFlexion(Movement):
    """Shoulder flexion movement analyzer"""
    
    @property
    def name(self) -> str:
        return "shoulder_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["RShoulder", "RElbow", "Hip", "Neck"]
    
    @property
    def primary_angle(self) -> str:
        return "shoulder"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 180)  # Normal flexion range
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate shoulder flexion angle"""
        angles = {}
        
        # Add virtual keypoints if needed
        keypoints = add_virtual_keypoints(keypoints)
        
        # Check if all required keypoints are present
        if not all(kp in keypoints for kp in self.required_keypoints):
            return angles
        
        # Calculate shoulder angle using Sports2D method
        shoulder_angle = compute_angle('right shoulder', keypoints, flip_left_right=False)
        if not np.isnan(shoulder_angle):
            angles["shoulder"] = shoulder_angle
        
        # Additional angles for context
        # Trunk angle to understand body position
        if all(k in keypoints for k in ["Neck", "Hip"]):
            trunk_angle = calculate_angle_between_points(
                keypoints["Hip"], 
                keypoints["Neck"],
                reference="vertical"
            )
            angles["trunk"] = trunk_angle
        
        # Elbow angle for arm position
        if all(k in keypoints for k in ["RShoulder", "RElbow", "RWrist"]):
            elbow_angle = compute_angle('right elbow', keypoints, flip_left_right=False)
            if not np.isnan(elbow_angle):
                angles["elbow"] = elbow_angle
        
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if person is in correct position for shoulder flexion measurement"""
        # Add virtual keypoints
        keypoints = add_virtual_keypoints(keypoints)
        
        # Check if all required keypoints are visible
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if person is facing camera (side view is better for shoulder flexion)
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            # If shoulders are too wide, person is facing camera
            if shoulder_width > 150:  # pixels, adjust threshold as needed
                return True, "Good position - facing camera. Side view would be better for shoulder flexion."
        
        # Check if arm is visible
        if "RWrist" in keypoints:
            # Check if wrist is reasonably positioned
            wrist_shoulder_dist = np.linalg.norm(
                keypoints["RWrist"] - keypoints["RShoulder"]
            )
            if wrist_shoulder_dist < 30:  # Too close, arm might be hidden
                return False, "Please extend your arm away from your body"
        
        return True, "Position is correct"
    
    def get_movement_phase(self, angle: float) -> str:
        """Determine movement phase based on angle"""
        if angle < 0:
            return "hyperextension"
        elif angle < 45:
            return "initial_flexion"
        elif angle < 90:
            return "mid_flexion"
        elif angle < 135:
            return "high_flexion"
        elif angle <= 180:
            return "full_flexion"
        else:
            return "hyperflexion"