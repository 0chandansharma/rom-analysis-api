from typing import Dict, Type
from app.core.body_parts.base import Movement

# Import all movements
from app.core.body_parts.lower_back.flexion import LowerBackFlexion
from app.core.body_parts.lower_back.extension import LowerBackExtension
from app.core.body_parts.lower_back.lateral_flexion import LowerBackLateralFlexion
from app.core.body_parts.lower_back.rotation import LowerBackRotation

class MovementRegistry:
    """Registry for all body part movements"""
    
    _movements: Dict[str, Dict[str, Type[Movement]]] = {}
    
    @classmethod
    def register(cls, body_part: str, movement_type: str, movement_class: Type[Movement]):
        """Register a movement class"""
        if body_part not in cls._movements:
            cls._movements[body_part] = {}
        cls._movements[body_part][movement_type] = movement_class
    
    @classmethod
    def get_movement(cls, body_part: str, movement_type: str) -> Type[Movement]:
        """Get movement class by body part and type"""
        if body_part not in cls._movements:
            raise ValueError(f"Unknown body part: {body_part}. Available: {list(cls._movements.keys())}")
        if movement_type not in cls._movements[body_part]:
            raise ValueError(f"Unknown movement type for {body_part}: {movement_type}. Available: {list(cls._movements[body_part].keys())}")
        return cls._movements[body_part][movement_type]
    
    @classmethod
    def list_movements(cls, body_part: str = None) -> Dict:
        """List available movements"""
        if body_part:
            return list(cls._movements.get(body_part, {}).keys())
        return {bp: list(movements.keys()) for bp, movements in cls._movements.items()}
    
    @classmethod
    def is_registered(cls, body_part: str, movement_type: str) -> bool:
        """Check if a movement is registered"""
        return body_part in cls._movements and movement_type in cls._movements[body_part]

# Register all lower back movements
MovementRegistry.register("lower_back", "flexion", LowerBackFlexion)
MovementRegistry.register("lower_back", "extension", LowerBackExtension)
MovementRegistry.register("lower_back", "lateral_flexion", LowerBackLateralFlexion)
MovementRegistry.register("lower_back", "rotation", LowerBackRotation)

# Placeholder registrations for other body parts (to be implemented)
# These will use the default angle calculations from ROMCalculator

# Shoulder movements
# MovementRegistry.register("shoulder", "flexion", ShoulderFlexion)
# MovementRegistry.register("shoulder", "extension", ShoulderExtension)
# MovementRegistry.register("shoulder", "abduction", ShoulderAbduction)
# MovementRegistry.register("shoulder", "adduction", ShoulderAdduction)
# MovementRegistry.register("shoulder", "internal_rotation", ShoulderInternalRotation)
# MovementRegistry.register("shoulder", "external_rotation", ShoulderExternalRotation)

# Elbow movements
# MovementRegistry.register("elbow", "flexion", ElbowFlexion)
# MovementRegistry.register("elbow", "extension", ElbowExtension)
# MovementRegistry.register("elbow", "pronation", ElbowPronation)
# MovementRegistry.register("elbow", "supination", ElbowSupination)

# Hip movements
# MovementRegistry.register("hip", "flexion", HipFlexion)
# MovementRegistry.register("hip", "extension", HipExtension)
# MovementRegistry.register("hip", "abduction", HipAbduction)
# MovementRegistry.register("hip", "adduction", HipAdduction)
# MovementRegistry.register("hip", "internal_rotation", HipInternalRotation)
# MovementRegistry.register("hip", "external_rotation", HipExternalRotation)

# Knee movements
# MovementRegistry.register("knee", "flexion", KneeFlexion)
# MovementRegistry.register("knee", "extension", KneeExtension)

# Ankle movements
# MovementRegistry.register("ankle", "dorsiflexion", AnkleDorsiflexion)
# MovementRegistry.register("ankle", "plantarflexion", AnklePlantarflexion)
# MovementRegistry.register("ankle", "inversion", AnkleInversion)
# MovementRegistry.register("ankle", "eversion", AnkleEversion)