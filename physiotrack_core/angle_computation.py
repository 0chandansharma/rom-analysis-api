"""
Complete angle computation functions for PhysioTrack
Includes ALL angle calculation strategies from Sports2D
"""
import numpy as np
from typing import Dict, List, Tuple, Optional, Union

# Complete angle definitions from 
ANGLE_DEFINITIONS = {
    # Joint angles
    'right ankle': {
        'points': ['RKnee', 'RAnkle', 'RBigToe', 'RHeel'],
        'type': 'dorsiflexion',
        'offset': 90,
        'scale': 1
    },
    'left ankle': {
        'points': ['LKnee', 'LAnkle', 'LBigToe', 'LHeel'],
        'type': 'dorsiflexion',
        'offset': 90,
        'scale': 1
    },
    'right knee': {
        'points': ['RAnkle', 'RKnee', 'RHip'],
        'type': 'flexion',
        'offset': -180,
        'scale': 1
    },
    'left knee': {
        'points': ['LAnkle', 'LKnee', 'LHip'],
        'type': 'flexion',
        'offset': -180,
        'scale': 1
    },
    'right hip': {
        'points': ['RKnee', 'RHip', 'Hip', 'Neck'],
        'type': 'flexion',
        'offset': 0,
        'scale': -1
    },
    'left hip': {
        'points': ['LKnee', 'LHip', 'Hip', 'Neck'],
        'type': 'flexion',
        'offset': 0,
        'scale': -1
    },
    'right shoulder': {
        'points': ['RElbow', 'RShoulder', 'Hip', 'Neck'],
        'type': 'flexion',
        'offset': 0,
        'scale': -1
    },
    'left shoulder': {
        'points': ['LElbow', 'LShoulder', 'Hip', 'Neck'],
        'type': 'flexion',
        'offset': 0,
        'scale': -1
    },
    'right elbow': {
        'points': ['RWrist', 'RElbow', 'RShoulder'],
        'type': 'flexion',
        'offset': 180,
        'scale': -1
    },
    'left elbow': {
        'points': ['LWrist', 'LElbow', 'LShoulder'],
        'type': 'flexion',
        'offset': 180,
        'scale': -1
    },
    'right wrist': {
        'points': ['RElbow', 'RWrist', 'RIndex'],
        'type': 'flexion',
        'offset': -180,
        'scale': 1
    },
    'left wrist': {
        'points': ['LElbow', 'LWrist', 'LIndex'],
        'type': 'flexion',
        'offset': -180,
        'scale': 1
    },
    
    # Segment angles
    'right foot': {
        'points': ['RBigToe', 'RHeel'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left foot': {
        'points': ['LBigToe', 'LHeel'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'right shank': {
        'points': ['RAnkle', 'RKnee'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left shank': {
        'points': ['LAnkle', 'LKnee'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'right thigh': {
        'points': ['RKnee', 'RHip'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left thigh': {
        'points': ['LKnee', 'LHip'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'pelvis': {
        'points': ['LHip', 'RHip'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'trunk': {
        'points': ['Neck', 'Hip'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'shoulders': {
        'points': ['LShoulder', 'RShoulder'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'head': {
        'points': ['Head', 'Neck'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'right arm': {
        'points': ['RElbow', 'RShoulder'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left arm': {
        'points': ['LElbow', 'LShoulder'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'right forearm': {
        'points': ['RWrist', 'RElbow'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left forearm': {
        'points': ['LWrist', 'LElbow'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'right hand': {
        'points': ['RIndex', 'RWrist'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    },
    'left hand': {
        'points': ['LIndex', 'LWrist'],
        'type': 'horizontal',
        'offset': 0,
        'scale': -1
    }
}

def calculate_angle_between_points(p1: np.ndarray, p2: np.ndarray, reference: str = "vertical") -> float:
    """
    Calculate angle between two points relative to reference
    
    Args:
        p1: First point (start)
        p2: Second point (end)
        reference: "vertical" or "horizontal"
    
    Returns:
        Angle in degrees
    """
    vector = p2 - p1
    
    if reference == "vertical":
        # Angle from vertical axis (positive Y points down)
        angle = np.degrees(np.arctan2(vector[0], -vector[1]))
    elif reference == "horizontal":
        # Angle from horizontal axis
        angle = np.degrees(np.arctan2(vector[1], vector[0]))
    else:
        raise ValueError(f"Unknown reference: {reference}")
    
    return float(angle)

def points_to_angles(points_list: List[np.ndarray]) -> float:
    """
    Original PhysioTrack angle calculation
    If len(points_list)==2, computes clockwise angle of ab vector w.r.t. horizontal
    If len(points_list)==3, computes clockwise angle from a to c around b
    If len(points_list)==4, computes clockwise angle between vectors ab and cd
    """
    if len(points_list) < 2:
        return np.nan
    
    points_array = np.array(points_list)
    dimensions = points_array.shape[-1] if len(points_array.shape) > 1 else 2
    
    if len(points_list) == 2:
        vector_u = points_array[0] - points_array[1]
        vector_v = np.array([1, 0, 0]) if dimensions == 3 else np.array([1, 0])
        
    elif len(points_list) == 3:
        vector_u = points_array[0] - points_array[1]
        vector_v = points_array[2] - points_array[1]
        
    elif len(points_list) == 4:
        vector_u = points_array[1] - points_array[0]
        vector_v = points_array[3] - points_array[2]
    else:
        return np.nan
    
    if dimensions == 2:
        vector_u = vector_u[:2]
        vector_v = vector_v[:2]
        ang = np.arctan2(vector_u[1], vector_u[0]) - np.arctan2(vector_v[1], vector_v[0])
    else:
        cross_product = np.cross(vector_u, vector_v)
        dot_product = np.dot(vector_u, vector_v)
        ang = np.arctan2(np.linalg.norm(cross_product), dot_product)
    
    ang_deg = np.degrees(ang)
    return float(ang_deg)

def fixed_angles(points_list: List[np.ndarray], angle_name: str) -> float:
    """
    Apply offset and multiplying factor to angles based on angle type
    """
    if angle_name not in ANGLE_DEFINITIONS:
        return np.nan
    
    ang = points_to_angles(points_list)
    if np.isnan(ang):
        return ang
    
    angle_def = ANGLE_DEFINITIONS[angle_name]
    ang += angle_def['offset']
    ang *= angle_def['scale']
    
    # Normalize angles
    if angle_name in ['pelvis', 'shoulders']:
        ang = np.where(ang > 90, ang - 180, ang)
        ang = np.where(ang < -90, ang + 180, ang)
    else:
        ang = np.where(ang > 180, ang - 360, ang)
        ang = np.where(ang < -180, ang + 360, ang)
    
    return float(ang)

def compute_angle(
    angle_name: str,
    keypoints: Dict[str, np.ndarray],
    flip_left_right: bool = True
) -> float:
    """
    Compute specific angle from keypoints dictionary
    """
    if angle_name not in ANGLE_DEFINITIONS:
        return np.nan
    
    angle_def = ANGLE_DEFINITIONS[angle_name]
    required_points = angle_def['points']
    
    # Check if all required keypoints are present
    if not all(pt in keypoints for pt in required_points):
        return np.nan
    
    # Get points
    points_list = [keypoints[pt] for pt in required_points]
    
    # Apply flipping if needed (for consistent left/right angles)
    if flip_left_right and any(pt.startswith(('L', 'R')) for pt in required_points):
        points_list = apply_flip_correction(points_list, required_points, keypoints)
    
    return fixed_angles(points_list, angle_name)

def apply_flip_correction(
    points_list: List[np.ndarray],
    point_names: List[str],
    keypoints: Dict[str, np.ndarray]
) -> List[np.ndarray]:
    """
    Apply left/right flip correction for consistent angle measurement
    """
    # Check foot direction if available
    if all(k in keypoints for k in ['LBigToe', 'LHeel', 'RBigToe', 'RHeel']):
        left_foot_dir = keypoints['LBigToe'][0] - keypoints['LHeel'][0]
        right_foot_dir = keypoints['RBigToe'][0] - keypoints['RHeel'][0]
        
        # Flip X coordinates if feet pointing left
        if left_foot_dir < 0 or right_foot_dir < 0:
            flipped_points = []
            for i, pt in enumerate(points_list):
                if point_names[i].startswith(('L', 'R')):
                    flipped_pt = pt.copy()
                    flipped_pt[0] = -flipped_pt[0]
                    flipped_points.append(flipped_pt)
                else:
                    flipped_points.append(pt)
            return flipped_points
    
    return points_list

def calculate_all_angles(
    keypoints: Dict[str, np.ndarray],
    angle_subset: List[str] = None
) -> Dict[str, float]:
    """
    Calculate all angles or a subset from keypoints
    """
    if angle_subset is None:
        angle_subset = list(ANGLE_DEFINITIONS.keys())
    
    angles = {}
    for angle_name in angle_subset:
        angle_value = compute_angle(angle_name, keypoints)
        if not np.isnan(angle_value):
            angles[angle_name] = angle_value
    
    return angles

def get_angle_requirements(angle_name: str) -> Dict[str, any]:
    """
    Get requirements for a specific angle calculation
    """
    if angle_name in ANGLE_DEFINITIONS:
        return ANGLE_DEFINITIONS[angle_name]
    return None

def mean_angles(angles_list: List[float]) -> float:
    """
    Calculate mean of angles (handling circular nature)
    """
    if not angles_list:
        return np.nan
    
    # Convert to radians
    angles_rad = np.radians(angles_list)
    
    # Calculate mean using circular statistics
    mean_sin = np.mean(np.sin(angles_rad))
    mean_cos = np.mean(np.cos(angles_rad))
    mean_angle = np.degrees(np.arctan2(mean_sin, mean_cos))
    
    return float(mean_angle)

def add_virtual_keypoints(keypoints: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Add computed keypoints like Neck and Hip if not present
    """
    keypoints = keypoints.copy()
    
    # Add Neck if not present
    if 'Neck' not in keypoints and all(k in keypoints for k in ['LShoulder', 'RShoulder']):
        keypoints['Neck'] = (keypoints['LShoulder'] + keypoints['RShoulder']) / 2
    
    # Add Hip if not present
    if 'Hip' not in keypoints and all(k in keypoints for k in ['LHip', 'RHip']):
        keypoints['Hip'] = (keypoints['LHip'] + keypoints['RHip']) / 2
    
    return keypoints