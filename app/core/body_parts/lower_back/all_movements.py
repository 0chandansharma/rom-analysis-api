# app/core/body_parts/lower_back/all_movements.py
import numpy as np
from typing import Dict, List, Tuple
from app.core.body_parts.base import Movement
from physiotrack_core.angle_computation import calculate_all_angles
from physiotrack_core.rom_calculations import ROMCalculator

class LowerBackFlexion(Movement):
    """Lower back flexion movement analyzer"""
    
    @property
    def name(self) -> str:
        return "lower_back_flexion"
    
    @property
    def required_keypoints(self) -> List[str]:
        return ROMCalculator.get_movement_requirements("lower_back", "flexion")
    
    @property
    def primary_angle(self) -> str:
        return "trunk"
    
    @property
    def normal_range(self) -> Tuple[float, float]:
        return (0, 60)
    
    def calculate_angles(self, keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
        """Calculate angles using ROMCalculator"""
        return ROMCalculator.calculate_movement_angles(
            keypoints, "lower_back", "flexion"
        )
    
    def validate_position(self, keypoints: Dict[str, np.ndarray]) -> Tuple[bool, str]:
        """Validate if person is in correct position"""
        missing = [k for k in self.required_keypoints if k not in keypoints]
        if missing:
            return False, f"Cannot detect: {', '.join(missing)}"
        
        # Check if person is facing camera
        if all(k in keypoints for k in ["LShoulder", "RShoulder"]):
            shoulder_width = np.linalg.norm(
                keypoints["LShoulder"] - keypoints["RShoulder"]
            )
            if shoulder_width < 50:  # pixels
                return False, "Please face the camera directly"
        
        return True, "Position is correct"