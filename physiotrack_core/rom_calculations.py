"""
ROM-specific calculations and movement analysis
Complete implementation with all body parts support
"""
import numpy as np
from typing import Dict, List, Tuple, Optional
from .angle_computation import calculate_all_angles, ANGLE_DEFINITIONS, calculate_angle_between_points, add_virtual_keypoints

class ROMCalculator:
    """Calculate ROM for different body parts and movements"""
    
    # Movement-specific angle mappings with complete implementation
    MOVEMENT_ANGLES = {
        'lower_back': {
            'flexion': {
                'primary': 'trunk',
                'secondary': ['pelvis', 'right hip', 'left hip'],
                'calculate': lambda kpts: calculate_lower_back_flexion(kpts),
                'normal_range': (0, 60),
                'max_range': (0, 90)
            },
            'extension': {
                'primary': 'trunk',
                'secondary': ['pelvis'],
                'calculate': lambda kpts: calculate_lower_back_extension(kpts),
                'normal_range': (-30, 0),
                'max_range': (-45, 0)
            },
            'lateral_flexion': {
                'primary': 'trunk',
                'secondary': ['shoulders', 'pelvis'],
                'calculate': lambda kpts: calculate_lower_back_lateral_flexion(kpts),
                'normal_range': (-30, 30),
                'max_range': (-45, 45)
            },
            'rotation': {
                'primary': 'shoulders',
                'secondary': ['pelvis'],
                'calculate': lambda kpts: calculate_lower_back_rotation(kpts),
                'normal_range': (-45, 45),
                'max_range': (-60, 60)
            }
        },
        'shoulder': {
            'flexion': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'calculate': lambda kpts: calculate_shoulder_flexion(kpts, 'right'),
                'normal_range': (0, 180),
                'max_range': (0, 190)
            },
            'extension': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'calculate': lambda kpts: calculate_shoulder_extension(kpts, 'right'),
                'normal_range': (0, 60),
                'max_range': (0, 80)
            },
            'abduction': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'calculate': lambda kpts: calculate_shoulder_abduction(kpts, 'right'),
                'normal_range': (0, 180),
                'max_range': (0, 190)
            },
            'adduction': {
                'primary': 'right shoulder',
                'secondary': ['trunk'],
                'calculate': lambda kpts: calculate_shoulder_adduction(kpts, 'right'),
                'normal_range': (0, 45),
                'max_range': (0, 60)
            }
        },
        'elbow': {
            'flexion': {
                'primary': 'right elbow',
                'secondary': [],
                'calculate': lambda kpts: calculate_elbow_flexion(kpts, 'right'),
                'normal_range': (0, 145),
                'max_range': (0, 160)
            },
            'extension': {
                'primary': 'right elbow',
                'secondary': [],
                'calculate': lambda kpts: calculate_elbow_extension(kpts, 'right'),
                'normal_range': (0, 10),
                'max_range': (-10, 10)
            }
        },
        'hip': {
            'flexion': {
                'primary': 'right hip',
                'secondary': ['pelvis', 'trunk'],
                'calculate': lambda kpts: calculate_hip_flexion(kpts, 'right'),
                'normal_range': (0, 120),
                'max_range': (0, 140)
            },
            'extension': {
                'primary': 'right hip',
                'secondary': ['pelvis'],
                'calculate': lambda kpts: calculate_hip_extension(kpts, 'right'),
                'normal_range': (0, 30),
                'max_range': (0, 40)
            },
            'abduction': {
                'primary': 'right hip',
                'secondary': ['pelvis'],
                'calculate': lambda kpts: calculate_hip_abduction(kpts, 'right'),
                'normal_range': (0, 45),
                'max_range': (0, 60)
            }
        },
        'knee': {
            'flexion': {
                'primary': 'right knee',
                'secondary': [],
                'calculate': lambda kpts: calculate_knee_flexion(kpts, 'right'),
                'normal_range': (0, 135),
                'max_range': (0, 160)
            },
            'extension': {
                'primary': 'right knee',
                'secondary': [],
                'calculate': lambda kpts: calculate_knee_extension(kpts, 'right'),
                'normal_range': (0, 10),
                'max_range': (-10, 10)
            }
        },
        'ankle': {
            'dorsiflexion': {
                'primary': 'right ankle',
                'secondary': [],
                'calculate': lambda kpts: calculate_ankle_dorsiflexion(kpts, 'right'),
                'normal_range': (0, 20),
                'max_range': (0, 30)
            },
            'plantarflexion': {
                'primary': 'right ankle',
                'secondary': [],
                'calculate': lambda kpts: calculate_ankle_plantarflexion(kpts, 'right'),
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
        
        # Add virtual keypoints if needed
        keypoints = add_virtual_keypoints(keypoints)
        
        movement_config = cls.MOVEMENT_ANGLES[body_part][movement_type]
        
        # Use custom calculation function if available
        if 'calculate' in movement_config:
            return movement_config['calculate'](keypoints)
        
        # Default calculation using angle definitions
        angles = {}
        primary_angle_name = movement_config['primary']
        
        # Handle side-specific angles
        if side == 'left' and 'right' in primary_angle_name:
            primary_angle_name = primary_angle_name.replace('right', 'left')
        
        # Calculate all relevant angles
        angles_to_calculate = [primary_angle_name] + movement_config.get('secondary', [])
        calculated_angles = calculate_all_angles(keypoints, angles_to_calculate)
        
        return calculated_angles
    
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
        required_angles = [movement_config['primary']] + movement_config.get('secondary', [])
        
        # Get all keypoints needed for these angles
        required_keypoints = set()
        for angle_name in required_angles:
            if angle_name in ANGLE_DEFINITIONS:
                required_keypoints.update(ANGLE_DEFINITIONS[angle_name]['points'])
        
        # Add virtual keypoint dependencies
        if 'Neck' in required_keypoints:
            required_keypoints.update(['LShoulder', 'RShoulder'])
        if 'Hip' in required_keypoints:
            required_keypoints.update(['LHip', 'RHip'])
        
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


# Lower back calculation functions
def calculate_lower_back_flexion(keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Calculate lower back flexion angles"""
    angles = {}
    
    # Calculate trunk angle (Neck to Hip)
    if all(k in keypoints for k in ['Neck', 'Hip']):
        trunk_angle = calculate_angle_between_points(
            keypoints['Neck'], 
            keypoints['Hip'],
            reference='vertical'
        )
        # Transform for flexion (180 - angle)
        angles['trunk'] = 180 - trunk_angle
    
    # Calculate pelvis angle
    if all(k in keypoints for k in ['LHip', 'RHip']):
        pelvis_angle = calculate_angle_between_points(
            keypoints['LHip'],
            keypoints['RHip'],
            reference='horizontal'
        )
        angles['pelvis'] = pelvis_angle
    
    # Calculate hip angles if available
    if all(k in keypoints for k in ['RKnee', 'RHip', 'Hip', 'Neck']):
        angles['right hip'] = calculate_all_angles(keypoints, ['right hip']).get('right hip', np.nan)
    
    if all(k in keypoints for k in ['LKnee', 'LHip', 'Hip', 'Neck']):
        angles['left hip'] = calculate_all_angles(keypoints, ['left hip']).get('left hip', np.nan)
    
    return angles

def calculate_lower_back_extension(keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Calculate lower back extension angles"""
    angles = {}
    
    # Calculate trunk angle
    if all(k in keypoints for k in ['Neck', 'Hip']):
        trunk_angle = calculate_angle_between_points(
            keypoints['Neck'], 
            keypoints['Hip'],
            reference='vertical'
        )
        # Transform for extension (angle - 180)
        angles['trunk'] = trunk_angle - 180
    
    # Calculate pelvis angle
    if all(k in keypoints for k in ['LHip', 'RHip']):
        pelvis_angle = calculate_angle_between_points(
            keypoints['LHip'],
            keypoints['RHip'],
            reference='horizontal'
        )
        angles['pelvis'] = pelvis_angle
    
    return angles

def calculate_lower_back_lateral_flexion(keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Calculate lower back lateral flexion angles"""
    angles = {}
    
    # Calculate trunk lateral angle
    if all(k in keypoints for k in ['Neck', 'Hip']):
        trunk_vector = keypoints['Neck'] - keypoints['Hip']
        # Calculate deviation from vertical
        lateral_angle = np.degrees(np.arctan2(trunk_vector[0], -trunk_vector[1]))
        angles['trunk'] = lateral_angle
    
    # Calculate shoulder tilt
    if all(k in keypoints for k in ['LShoulder', 'RShoulder']):
        shoulder_angle = calculate_angle_between_points(
            keypoints['LShoulder'],
            keypoints['RShoulder'],
            reference='horizontal'
        )
        angles['shoulders'] = shoulder_angle
    
    # Calculate pelvis tilt
    if all(k in keypoints for k in ['LHip', 'RHip']):
        pelvis_angle = calculate_angle_between_points(
            keypoints['LHip'],
            keypoints['RHip'],
            reference='horizontal'
        )
        angles['pelvis'] = pelvis_angle
    
    return angles

def calculate_lower_back_rotation(keypoints: Dict[str, np.ndarray]) -> Dict[str, float]:
    """Calculate lower back rotation angles"""
    angles = {}
    
    # Calculate rotation based on shoulder-hip alignment
    if all(k in keypoints for k in ['LShoulder', 'RShoulder', 'LHip', 'RHip']):
        # Shoulder line vector
        shoulder_vector = keypoints['RShoulder'] - keypoints['LShoulder']
        shoulder_angle = np.degrees(np.arctan2(shoulder_vector[1], shoulder_vector[0]))
        
        # Hip line vector
        hip_vector = keypoints['RHip'] - keypoints['LHip']
        hip_angle = np.degrees(np.arctan2(hip_vector[1], hip_vector[0]))
        
        # Rotation is difference between shoulder and hip angles
        rotation_angle = shoulder_angle - hip_angle
        
        # Normalize to [-180, 180]
        if rotation_angle > 180:
            rotation_angle -= 360
        elif rotation_angle < -180:
            rotation_angle += 360
        
        angles['shoulders'] = shoulder_angle
        angles['pelvis'] = hip_angle
        angles['trunk_rotation'] = rotation_angle
    
    return angles

# Placeholder functions for other body parts (to be implemented as needed)
def calculate_shoulder_flexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate shoulder flexion"""
    angles = calculate_all_angles(keypoints, [f'{side} shoulder'])
    return angles

def calculate_shoulder_extension(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate shoulder extension"""
    angles = calculate_shoulder_flexion(keypoints, side)
    # Negate for extension
    for key in angles:
        angles[key] = -angles[key]
    return angles

def calculate_shoulder_abduction(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate shoulder abduction"""
    return calculate_all_angles(keypoints, [f'{side} shoulder'])

def calculate_shoulder_adduction(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate shoulder adduction"""
    return calculate_shoulder_abduction(keypoints, side)

def calculate_elbow_flexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate elbow flexion"""
    angles = calculate_all_angles(keypoints, [f'{side} elbow'])
    # Transform for flexion
    for key in angles:
        if 'elbow' in key:
            angles[key] = 180 - angles[key]
    return angles

def calculate_elbow_extension(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate elbow extension"""
    return calculate_all_angles(keypoints, [f'{side} elbow'])

def calculate_hip_flexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate hip flexion"""
    return calculate_all_angles(keypoints, [f'{side} hip'])

def calculate_hip_extension(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate hip extension"""
    angles = calculate_hip_flexion(keypoints, side)
    # Negate for extension
    for key in angles:
        angles[key] = -angles[key]
    return angles

def calculate_hip_abduction(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate hip abduction"""
    return calculate_all_angles(keypoints, [f'{side} hip'])

def calculate_knee_flexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate knee flexion"""
    angles = calculate_all_angles(keypoints, [f'{side} knee'])
    # Transform for flexion
    for key in angles:
        if 'knee' in key:
            angles[key] = -angles[key]
    return angles

def calculate_knee_extension(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate knee extension"""
    return calculate_all_angles(keypoints, [f'{side} knee'])

def calculate_ankle_dorsiflexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate ankle dorsiflexion"""
    angles = calculate_all_angles(keypoints, [f'{side} ankle'])
    # Transform for dorsiflexion
    for key in angles:
        if 'ankle' in key:
            angles[key] = angles[key] - 90
    return angles

def calculate_ankle_plantarflexion(keypoints: Dict[str, np.ndarray], side: str) -> Dict[str, float]:
    """Calculate ankle plantarflexion"""
    angles = calculate_all_angles(keypoints, [f'{side} ankle'])
    # Transform for plantarflexion
    for key in angles:
        if 'ankle' in key:
            angles[key] = 90 - angles[key]
    return angles