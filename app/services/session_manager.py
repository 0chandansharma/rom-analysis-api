from typing import Optional, Dict
from app.core.rom.tracker import ROMTracker
from app.storage.interface import StorageInterface

class SessionManager:
    """Manage ROM tracking sessions"""
    
    def __init__(self, storage: StorageInterface):
        self.storage = storage
    
    async def get_or_create_tracker(
        self, 
        session_id: str, 
        body_part: str, 
        movement_type: str
    ) -> ROMTracker:
        """Get existing tracker or create new one"""
        tracker_key = f"{session_id}:{body_part}:{movement_type}"
        
        # Try to get existing tracker
        tracker_data = await self.storage.get(tracker_key)
        
        if tracker_data:
            # Reconstruct tracker from stored data
            tracker = ROMTracker(body_part, movement_type)
            tracker.min_angle = tracker_data.get("min_angle")
            tracker.max_angle = tracker_data.get("max_angle")
            tracker.frame_count = tracker_data.get("frame_count", 0)
            tracker.valid_frame_count = tracker_data.get("valid_frame_count", 0)
        else:
            # Create new tracker
            tracker = ROMTracker(body_part, movement_type)
        
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
            "movement_type": tracker.movement_type
        }
        
        await self.storage.set(tracker_key, tracker_data)
    
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
            # Extract body_part and movement_type from key
            parts = key.split(":")
            if len(parts) == 3:
                body_part = parts[1]
                movement_type = parts[2]
                
                if body_part not in session_data["trackers"]:
                    session_data["trackers"][body_part] = {}
                
                session_data["trackers"][body_part][movement_type] = {
                    "rom": {
                        "min": data.get("min_angle", 0),
                        "max": data.get("max_angle", 0),
                        "range": (data.get("max_angle", 0) - data.get("min_angle", 0)) if data.get("min_angle") else 0
                    },
                    "frame_count": data.get("frame_count", 0),
                    "valid_frame_count": data.get("valid_frame_count", 0)
                }
        
        return session_data
    
    async def clear_session(self, session_id: str):
        """Clear all data for a session"""
        pattern = f"{session_id}:*"
        await self.storage.delete_pattern(pattern)