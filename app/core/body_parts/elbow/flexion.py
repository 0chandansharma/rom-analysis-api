import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import compute_angle, add_virtual_keypoints

class ElbowFlexion(Movement):
    """Elbow flexion movement analyzer"""
    
    @property
    def name(self) -> str:
        return "elbow_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["RShoulder", "RElbow", "RWrist"]
    
    @property
    def primary_angle(self) -> str:
        return "elbow"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 145)  # Normal flexion range
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate elbow flexion angle"""
        angles = {}
        
        # Add virtual keypoints if needed
        keypoints = add_virtual_keypoints(keypoints)
        
        # Check if all required keypoints are present
        if not all(kp in keypoints for kp in self.required_keypoints):
            return angles
        
        # Calculate elbow angle using  method
        elbow_angle_raw = compute_angle('right elbow', keypoints, flip_left_right=False)
        
        if not np.isnan(elbow_angle_raw):
            # Convert to flexion angle (0° = full extension, 145° = full flexion)
            # uses offset of 180 and scale of -1 for elbow
            elbow_flexion = 180 - elbow_angle_raw
            angles["elbow"] = max(0, min(180, elbow_flexion))  # Clamp to reasonable range
            
        # Additional context angles
        # Shoulder angle to understand arm position
        if all(k in keypoints for k in ["RElbow", "RShoulder", "Hip", "Neck"]):
            shoulder_angle = compute_angle('right shoulder', keypoints, flip_left_right=False)
            if not np.isnan(shoulder_angle):
                angles["shoulder"] = shoulder_angle
        
        # Forearm rotation indicator (if hand keypoints available)
        if all(k in keypoints for k in ["RWrist", "RElbow", "RIndex"]):
            wrist_angle = compute_angle('right wrist', keypoints, flip_left_right=False)
            if not np.isnan(wrist_angle):
                angles["wrist"] = wrist_angle
                
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if person is in correct position for elbow flexion measurement"""
        # Add virtual keypoints
        keypoints = add_virtual_keypoints(keypoints)
        
        # Check if all required keypoints are visible
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if arm is properly visible
        shoulder_elbow_dist = np.linalg.norm(
            keypoints["RElbow"] - keypoints["RShoulder"]
        )
        elbow_wrist_dist = np.linalg.norm(
            keypoints["RWrist"] - keypoints["RElbow"]
        )
        
        # Check if segments are too short (arm might be pointing toward/away from camera)
        min_segment_length = 50  # pixels
        if shoulder_elbow_dist < min_segment_length:
            return False, "Upper arm is not clearly visible. Please position your arm parallel to the camera."
        if elbow_wrist_dist < min_segment_length:
            return False, "Forearm is not clearly visible. Please position your arm parallel to the camera."
        
        # Check arm position relative to body
        if "LShoulder" in keypoints:
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            # Arm should be somewhat away from body for clear measurement
            if shoulder_elbow_dist < shoulder_width * 0.3:
                return False, "Please move your arm slightly away from your body"
        
        return True, "Position is correct"
    
    def get_movement_phase(self, angle: float) -> str:
        """Determine movement phase based on angle"""
        if angle < 10:
            return "full_extension"
        elif angle < 30:
            return "near_extension"
        elif angle < 60:
            return "slight_flexion"
        elif angle < 90:
            return "moderate_flexion"
        elif angle < 120:
            return "significant_flexion"
        elif angle < 145:
            return "near_full_flexion"
        else:
            return "full_flexion"

class ElbowExtension(Movement):
    """Elbow extension movement analyzer (reverse of flexion)"""
    
    @property
    def name(self) -> str:
        return "elbow_extension"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ["RShoulder", "RElbow", "RWrist"]
    
    @property
    def primary_angle(self) -> str:
        return "elbow"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 10)  # Normal hyperextension range
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate elbow extension angle"""
        angles = {}
        
        # Use the same calculation as flexion
        flexion_calc = ElbowFlexion()
        flexion_angles = flexion_calc.calculate_angles(keypoints)
        
        if "elbow" in flexion_angles:
            # Extension is measured as deviation from straight (180°)
            # Negative values indicate hyperextension
            extension_angle = 180 - flexion_angles["elbow"]
            angles["elbow"] = extension_angle
            
            # Include other angles for context
            if "shoulder" in flexion_angles:
                angles["shoulder"] = flexion_angles["shoulder"]
            if "wrist" in flexion_angles:
                angles["wrist"] = flexion_angles["wrist"]
                
        return angles
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Same validation as flexion"""
        return ElbowFlexion().validate_position(keypoints)
    
    def get_movement_phase(self, angle: float) -> str:
        """Determine movement phase based on extension angle"""
        if angle < -10:
            return "excessive_hyperextension"
        elif angle < 0:
            return "hyperextension"
        elif angle < 5:
            return "full_extension"
        elif angle < 15:
            return "slight_flexion"
        else:
            return "flexed"