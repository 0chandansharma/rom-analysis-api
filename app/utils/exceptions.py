class ROMAnalysisError(Exception):
    """Base exception for ROM analysis"""
    pass

class PoseDetectionError(ROMAnalysisError):
    """Error in pose detection"""
    pass

class AngleCalculationError(ROMAnalysisError):
    """Error in angle calculation"""
    pass

class AnalysisError(ROMAnalysisError):
    """General analysis error"""
    pass

class InvalidFrameError(ROMAnalysisError):
    """Invalid frame data"""
    pass

class SessionNotFoundError(ROMAnalysisError):
    """Session not found"""
    pass