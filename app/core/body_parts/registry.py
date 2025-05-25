from typing import Dict, Type
from app.core.body_parts.base import Movement

# Import all movements
from app.core.body_parts.lower_back.flexion import LowerBackFlexion
from app.core.body_parts.lower_back.extension import LowerBackExtension
# Add more imports as you implement them

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
            raise ValueError(f"Unknown body part: {body_part}")
        if movement_type not in cls._movements[body_part]:
            raise ValueError(f"Unknown movement type for {body_part}: {movement_type}")
        return cls._movements[body_part][movement_type]
    
    @classmethod
    def list_movements(cls, body_part: str = None) -> Dict:
        """List available movements"""
        if body_part:
            return list(cls._movements.get(body_part, {}).keys())
        return {bp: list(movements.keys()) for bp, movements in cls._movements.items()}

# Register all movements
MovementRegistry.register("lower_back", "flexion", LowerBackFlexion)
MovementRegistry.register("lower_back", "extension", LowerBackExtension)
# Add more registrations as you implement them