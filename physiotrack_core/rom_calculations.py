"""
ROM-specific calculations and movement analysis
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from .angle_computation import calculate_all_angles, ANGLE_DEFINITIONS

class ROMCalculator:
    """Calculate ROM for different body parts and movements"""
    
    # Movement-specific angle mappings
    MOVEMENT_ANGLES = {
        'lower_back': {
            'flexion': {
                'primary': 'trunk',
                'secondary': ['pelvis', 'right hip', 'left hip'],
                'transform': lambda x: 180 - x,  # Flexion is 180 - trunk angle
                'normal_range': (0, 60),
                'max_range': (0, 90)
            },
            'extension': {
                'primary': 'trunk',
                'secondary': ['pelvis'],
                'transform': lambda x: x - 180,  # Extension is trunk angle - 180
                'normal_range': (-30, 0),
                'max_range': (-45, 0)
            },
            'lateral_flexion': {
                'primary': 'trunk',
                'secondary': ['shoulders', 'pelvis'],
                'transform': lambda x: x,  # Direct lateral angle
                'normal_range': (-30, 30),
                'max_range': (-45, 45)
            },
            'rotation': {
                'primary': 'shoulders',
                'secondary': ['pelvis'],
                'transform': lambda x: x,  # Shoulder-pelvis difference
                'normal_range': (-45, 45),
                'max_range': (-60, 60)
            }
        },
        'shoulder': {
            'flexion': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'transform': lambda x: x,
                'normal_range': (0, 180),
                'max_range': (0, 190)
            },
            'extension': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'transform': lambda x: -x,
                'normal_range': (0, 60),
                'max_range': (0, 80)
            },
            'abduction': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'transform': lambda x: x,
                'normal_range': (0, 180),
                'max_range': (0, 190)
            }
        },
        'elbow': {
            'flexion': {
                'primary': 'right elbow',
                'secondary': [],
                'transform': lambda x: 180 - x,
                'normal_range': (0, 145),
                'max_range': (0, 160)
            },
            'extension': {
                'primary': 'right elbow',
                'secondary': [],
                'transform': lambda x: x,
                'normal_range': (0, 10),
                'max_range': (-10, 10)
            }
        },
        'hip': {
            'flexion': {
                'primary': 'right hip',
                'secondary': ['pelvis', 'trunk'],
                'transform': lambda x: x,
                'normal_range': (0, 120),
                'max_range': (0, 140)
            },
            'extension': {
                'primary': 'right hip',
                'secondary': ['pelvis'],
                'transform': lambda x: -x,
                'normal_range': (0, 30),
                'max_range': (0, 40)
            },
            'abduction': {
                'primary': 'right hip',
                'secondary': ['pelvis'],
                'transform': lambda x: x,
                'normal_range': (0, 45),
                'max_range': (0, 60)
            }
        },
        'knee': {
            'flexion': {
                'primary': 'right knee',
                'secondary': [],
                'transform': lambda x: -x,  # Knee flexion is negative
                'normal_range': (0, 135),
                'max_range': (0, 160)
            },
            'extension': {
                'primary': 'right knee',
                'secondary': [],
                'transform': lambda x: x,
                'normal_range': (0, 10),
                'max_range': (-10, 10)
            }
        },
        'ankle': {
            'dorsiflexion': {
                'primary': 'right ankle',
                'secondary': [],
                'transform': lambda x: x - 90,
                'normal_range': (0, 20),
                'max_range': (0, 30)
            },
            'plantarflexion': {
                'primary': 'right ankle',
                'secondary': [],
                'transform': lambda x: 90 - x,
                'normal_range': (0, 50),
                'max_range': (0, 60)
            }
        }
    }
    
    @classmethod
    def calculate_movement_angles(
        cls,
        keypoints: Dict[str, np.ndarray],
        body_part: str,
        movement_type: str,
        side: str = 'right'
    ) -> Dict[str, float]:
        """
        Calculate angles for specific movement
        """
        if body_part not in cls.MOVEMENT_ANGLES:
            raise ValueError(f"Unknown body part: {body_part}")
        
        if movement_type not in cls.MOVEMENT_ANGLES[body_part]:
            raise ValueError(f"Unknown movement for {body_part}: {movement_type}")
        
        movement_config = cls.MOVEMENT_ANGLES[body_part][movement_type]
        angles = {}
        
        # Get primary angle
        primary_angle_name = movement_config['primary']
        
        # Handle side-specific angles
        if side == 'left' and 'right' in primary_angle_name:
            primary_angle_name = primary_angle_name.replace('right', 'left')
        
        # Calculate all relevant angles
        angles_to_calculate = [primary_angle_name] + movement_config['secondary']
        calculated_angles = calculate_all_angles(keypoints, angles_to_calculate)
        
        # Apply transformations
        for angle_name, angle_value in calculated_angles.items():
            if angle_name == primary_angle_name:
                transformed_value = movement_config['transform'](angle_value)
                angles[angle_name] = transformed_value
            else:
                angles[angle_name] = angle_value
        
        return angles
    
    @classmethod
    def get_movement_requirements(cls, body_part: str, movement_type: str) -> List[str]:
        """
        Get required keypoints for a movement
        """
        if body_part not in cls.MOVEMENT_ANGLES:
            return []
        
        if movement_type not in cls.MOVEMENT_ANGLES[body_part]:
            return []
        
        movement_config = cls.MOVEMENT_ANGLES[body_part][movement_type]
        required_angles = [movement_config['primary']] + movement_config['secondary']
        
        # Get all keypoints needed for these angles
        required_keypoints = set()
        for angle_name in required_angles:
            if angle_name in ANGLE_DEFINITIONS:
                required_keypoints.update(ANGLE_DEFINITIONS[angle_name]['points'])
        
        return list(required_keypoints)
    
    @classmethod
    def validate_rom(
        cls,
        angle_value: float,
        body_part: str,
        movement_type: str
    ) -> Dict[str, any]:
        """
        Validate if ROM is within normal/safe ranges
        """
        if body_part not in cls.MOVEMENT_ANGLES:
            return {'valid': False, 'message': 'Unknown body part'}
        
        if movement_type not in cls.MOVEMENT_ANGLES[body_part]:
            return {'valid': False, 'message': 'Unknown movement'}
        
        movement_config = cls.MOVEMENT_ANGLES[body_part][movement_type]
        normal_min, normal_max = movement_config['normal_range']
        max_min, max_max = movement_config['max_range']
        
        result = {
            'valid': True,
            'in_normal_range': normal_min <= angle_value <= normal_max,
            'in_max_range': max_min <= angle_value <= max_max,
            'normal_range': movement_config['normal_range'],
            'max_range': movement_config['max_range']
        }
        
        if angle_value < max_min:
            result['message'] = f"Angle {angle_value:.1f}° is below minimum safe range"
            result['valid'] = False
        elif angle_value > max_max:
            result['message'] = f"Angle {angle_value:.1f}° exceeds maximum safe range"
            result['valid'] = False
        elif not result['in_normal_range']:
            result['message'] = f"Angle {angle_value:.1f}° is outside normal range"
        else:
            result['message'] = "Angle is within normal range"
        
        return result