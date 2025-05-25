from typing import Optional, Dict, List
from app.core.rom.tracker import ROMTracker
from app.storage.interface import StorageInterface
import json
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """Manage ROM tracking sessions"""
    
    def __init__(self, storage: StorageInterface):
        self.storage = storage
        self.trackers_cache = {}  # In-memory cache for active trackers
    
    async def get_or_create_tracker(
        self, 
        session_id: str, 
        body_part: str, 
        movement_type: str
    ) -> ROMTracker:
        """Get existing tracker or create new one"""
        tracker_key = f"{session_id}:{body_part}:{movement_type}"
        
        # Check in-memory cache first
        if tracker_key in self.trackers_cache:
            return self.trackers_cache[tracker_key]
        
        # Try to get existing tracker from storage
        tracker_data = await self.storage.get(tracker_key)
        
        if tracker_data:
            # Reconstruct tracker from stored data
            tracker = ROMTracker(body_part, movement_type)
            if isinstance(tracker_data, str):
                tracker_data = json.loads(tracker_data)
            
            tracker.min_angle = tracker_data.get("min_angle")
            tracker.max_angle = tracker_data.get("max_angle")
            tracker.frame_count = tracker_data.get("frame_count", 0)
            tracker.valid_frame_count = tracker_data.get("valid_frame_count", 0)
            
            # Restore angle history if available
            if "angle_history" in tracker_data:
                for angle in tracker_data["angle_history"]:
                    tracker.angle_history.append(angle)
        else:
            # Create new tracker
            tracker = ROMTracker(body_part, movement_type)
        
        # Cache the tracker
        self.trackers_cache[tracker_key] = tracker
        
        return tracker
    
    async def save_tracker(self, session_id: str, tracker: ROMTracker):
        """Save tracker state"""
        tracker_key = f"{session_id}:{tracker.body_part}:{tracker.movement_type}"
        
        tracker_data = {
            "min_angle": tracker.min_angle,
            "max_angle": tracker.max_angle,
            "frame_count": tracker.frame_count,
            "valid_frame_count": tracker.valid_frame_count,
            "body_part": tracker.body_part,
            "movement_type": tracker.movement_type,
            "angle_history": list(tracker.angle_history)  # Convert deque to list
        }
        
        # Save to storage with TTL
        await self.storage.set(tracker_key, json.dumps(tracker_data), ttl=3600)
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get all data for a session"""
        pattern = f"{session_id}:*"
        all_data = await self.storage.get_pattern(pattern)
        
        if not all_data:
            return None
        
        session_data = {
            "session_id": session_id,
            "trackers": {}
        }
        
        for key, data in all_data.items():
            # Parse JSON data if stored as string
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON for key {key}")
                    continue
            
            # Extract body_part and movement_type from key
            parts = key.split(":")
            if len(parts) >= 3:
                body_part = parts[1]
                movement_type = parts[2]
                
                if body_part not in session_data["trackers"]:
                    session_data["trackers"][body_part] = {}
                
                session_data["trackers"][body_part][movement_type] = {
                    "rom": {
                        "min": data.get("min_angle", 0),
                        "max": data.get("max_angle", 0),
                        "range": (data.get("max_angle", 0) - data.get("min_angle", 0)) if data.get("min_angle") is not None else 0,
                        "current": data.get("angle_history", [0])[-1] if data.get("angle_history") else 0
                    },
                    "frame_count": data.get("frame_count", 0),
                    "valid_frame_count": data.get("valid_frame_count", 0)
                }
        
        return session_data
    
    async def clear_session(self, session_id: str):
        """Clear all data for a session"""
        pattern = f"{session_id}:*"
        await self.storage.delete_pattern(pattern)
        
        # Clear from cache
        keys_to_remove = [k for k in self.trackers_cache.keys() if k.startswith(f"{session_id}:")]
        for key in keys_to_remove:
            del self.trackers_cache[key]
        
        logger.info(f"Cleared session {session_id}")
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        all_keys = await self.storage.get_pattern("*")
        session_ids = set()
        
        for key in all_keys:
            parts = key.split(":")
            if len(parts) >= 1:
                session_ids.add(parts[0])
        
        return list(session_ids)