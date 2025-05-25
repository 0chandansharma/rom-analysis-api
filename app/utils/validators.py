import base64
from typing import Tuple

def validate_base64_image(base64_string: str) -> Tuple[bool, str]:
    """Validate base64 encoded image"""
    try:
        # Check if it's a data URL
        if "," in base64_string:
            header, base64_string = base64_string.split(",", 1)
            # Validate image type from header
            if not any(img_type in header for img_type in ["image/jpeg", "image/png", "image/jpg"]):
                return False, "Invalid image type. Only JPEG and PNG are supported"
        
        # Try to decode
        img_data = base64.b64decode(base64_string)
        
        # Check if it's not empty
        if len(img_data) == 0:
            return False, "Empty image data"
        
        # Basic check for image headers
        if img_data[:2] == b'\xff\xd8':  # JPEG
            return True, "Valid JPEG"
        elif img_data[:8] == b'\x89PNG\r\n\x1a\n':  # PNG
            return True, "Valid PNG"
        else:
            return False, "Unknown image format"
            
    except Exception as e:
        return False, f"Invalid base64 encoding: {str(e)}"

def validate_session_id(session_id: str) -> Tuple[bool, str]:
    """Validate session ID format"""
    if not session_id:
        return False, "Session ID cannot be empty"
    
    if len(session_id) > 128:
        return False, "Session ID too long (max 128 characters)"
    
    # Allow alphanumeric, dash, underscore
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        return False, "Session ID can only contain letters, numbers, dash, and underscore"
    
    return True, "Valid"