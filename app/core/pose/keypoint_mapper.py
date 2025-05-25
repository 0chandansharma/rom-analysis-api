from typing import Dict, List

class KeypointMapper:
    """Map keypoints to body parts and validate requirements"""
    
    # Keypoint groups by body part
    BODY_PART_KEYPOINTS = {
        "lower_back": {
            "core": ["Neck", "Hip", "LShoulder", "RShoulder", "LHip", "RHip"],
            "optional": ["Head", "Pelvis"]
        },
        "shoulder": {
            "core": ["LShoulder", "RShoulder", "LElbow", "RElbow", "Neck"],
            "optional": ["LWrist", "RWrist"]
        },
        "elbow": {
            "core": ["LShoulder", "RShoulder", "LElbow", "RElbow", "LWrist", "RWrist"],
            "optional": []
        },
        "hip": {
            "core": ["LHip", "RHip", "LKnee", "RKnee", "Hip"],
            "optional": ["LAnkle", "RAnkle"]
        },
        "knee": {
            "core": ["LHip", "RHip", "LKnee", "RKnee", "LAnkle", "RAnkle"],
            "optional": ["LBigToe", "RBigToe"]
        },
        "ankle": {
            "core": ["LKnee", "RKnee", "LAnkle", "RAnkle", "LBigToe", "RBigToe"],
            "optional": ["LHeel", "RHeel", "LSmallToe", "RSmallToe"]
        }
    }
    
    @classmethod
    def get_required_keypoints(cls, body_part: str) -> List[str]:
        """Get required keypoints for a body part"""
        if body_part not in cls.BODY_PART_KEYPOINTS:
            raise ValueError(f"Unknown body part: {body_part}")
        return cls.BODY_PART_KEYPOINTS[body_part]["core"]
    
    @classmethod
    def validate_keypoints(cls, keypoints: Dict, body_part: str) -> bool:
        """Check if all required keypoints are present"""
        required = cls.get_required_keypoints(body_part)
        return all(kp in keypoints for kp in required)