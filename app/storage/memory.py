from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from app.storage.interface import StorageInterface

class InMemoryStorage(StorageInterface):
    """In-memory storage implementation"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._expiry: Dict[str, datetime] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        # Check expiry
        if key in self._expiry:
            if datetime.utcnow() > self._expiry[key]:
                await self.delete(key)
                return None
        
        return self._data.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value with optional TTL in seconds"""
        self._data[key] = value
        
        if ttl:
            self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)
        elif key in self._expiry:
            del self._expiry[key]
    
    async def delete(self, key: str):
        """Delete value by key"""
        if key in self._data:
            del self._data[key]
        if key in self._expiry:
            del self._expiry[key]
    
    async def get_pattern(self, pattern: str) -> Dict[str, Any]:
        """Get all keys matching pattern (simple wildcard support)"""
        # Simple pattern matching (supports * at end)
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return {
                k: v for k, v in self._data.items()
                if k.startswith(prefix)
            }
        return {pattern: self._data.get(pattern)} if pattern in self._data else {}
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        keys_to_delete = list(self.get_pattern(pattern).keys())
        for key in keys_to_delete:
            await self.delete(key)