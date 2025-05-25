# ===== app/core/body_parts/lower_back/extension.py =====
import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import add_virtual_keypoints
from physiotrack_core.rom_calculations import calculate_lower_back_extension as calc_extension

class LowerBackExtension(Movement):
    """Lower back extension movement analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_extension"
    
    @property
    def required_keypoints(self) -> List[str]:
        base = ["Neck", "Hip", "LHip", "RHip"]
        virtual = ["LShoulder", "RShoulder"]
        return base + virtual
    
    @property
    def primary_angle(self) -> str:
        return "trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (-30, 0)  # Normal extension range (negative values)
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate trunk and pelvis angles for extension"""
        keypoints = add_virtual_keypoints(keypoints)
        return calc_extension(keypoints)
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate position for extension measurement"""
        # Basic validation
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if person is facing camera
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            if shoulder_width < 50:
                return False, "Please face the camera directly"
        
        # Additional check for extension: trunk should be relatively upright
        if "trunk" in self.calculate_angles(keypoints):
            trunk_angle = self.calculate_angles(keypoints)["trunk"]
            if trunk_angle > 30:  # Too much flexion
                return False, "Please stand upright before extending"
        
        return True, "Position is correct"


