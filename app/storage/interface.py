from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class StorageInterface(ABC):
    """Abstract interface for storage backends"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with optional TTL"""
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        """Delete value by key"""
        pass
    
    @abstractmethod
    async def get_pattern(self, pattern: str) -> Dict[str, Any]:
        """Get all keys matching pattern"""
        pass
    
    @abstractmethod
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        pass