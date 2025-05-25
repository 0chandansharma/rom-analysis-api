# app/core/body_parts/lower_back/flexion.py
import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_angle_between_points, add_virtual_keypoints
from physiotrack_core.rom_calculations import calculate_lower_back_flexion as calc_flexion

class LowerBackFlexion(Movement):
    """Lower back flexion movement analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        # Base requirements
        base = ["Neck", "Hip", "LHip", "RHip"]
        # Additional for virtual keypoints
        virtual = ["LShoulder", "RShoulder"]
        return base + virtual
    
    @property
    def primary_angle(self) -> str:
        return "trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 60)  # Normal flexion range
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate trunk and pelvis angles for flexion"""
        # Add virtual keypoints if needed
        keypoints = add_virtual_keypoints(keypoints)
        
        # Use the centralized calculation function
        return calc_flexion(keypoints)
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if person is in correct position for flexion measurement"""
        # Check if all required keypoints are present
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if person is facing camera (frontal plane)
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            # If shoulders are too close, person might be sideways
            if shoulder_width < 50:  # pixels, adjust threshold as needed
                return False, "Please face the camera directly"
        
        return True, "Position is correct"

