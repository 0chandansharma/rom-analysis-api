#!/usr/bin/env python
"""
Check if all components can be initialized properly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_imports():
    """Check if all required imports work"""
    print("Checking imports...")
    
    try:
        import cv2
        print("✓ OpenCV imported successfully")
    except ImportError as e:
        print(f"✗ OpenCV import failed: {e}")
        return False
    
    try:
        import numpy as np
        print("✓ NumPy imported successfully")
    except ImportError as e:
        print(f"✗ NumPy import failed: {e}")
        return False
    
    try:
        import torch
        print(f"✓ PyTorch imported successfully (CUDA available: {torch.cuda.is_available()})")
    except ImportError as e:
        print(f"✗ PyTorch import failed: {e}")
        return False
    
    try:
        import rtmlib
        print("✓ RTMLib imported successfully")
    except ImportError as e:
        print(f"✗ RTMLib import failed: {e}")
        print("  Install with: pip install rtmlib")
        return False
    
    try:
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")
    except ImportError as e:
        print(f"✗ FastAPI import failed: {e}")
        return False
    
    return True

def check_pose_detector():
    """Check if pose detector can be initialized"""
    print("\nChecking pose detector initialization...")
    
    try:
        from physiotrack_core.pose_detection import PoseDetector
        print("✓ PoseDetector imported successfully")
        
        # Try to initialize
        detector = PoseDetector(
            model="body_with_feet",
            mode="performance",
            device="cpu",
            backend="onnxruntime"
        )
        print("✓ PoseDetector initialized successfully")
        
        # Check if it's ready
        if detector.is_initialized:
            print("✓ PoseDetector is ready for inference")
        else:
            print("✗ PoseDetector initialization incomplete")
            return False
            
    except Exception as e:
        print(f"✗ PoseDetector initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def check_movement_registry():
    """Check if movements are properly registered"""
    print("\nChecking movement registry...")
    
    try:
        from app.core.body_parts.registry import MovementRegistry
        
        movements = MovementRegistry.list_movements()
        print(f"✓ Movement registry loaded with {len(movements)} body parts")
        
        for body_part, movement_types in movements.items():
            print(f"  - {body_part}: {', '.join(movement_types)}")
        
        # Test getting a movement
        flexion = MovementRegistry.get_movement("lower_back", "flexion")
        print("✓ Can retrieve movement classes successfully")
        
    except Exception as e:
        print(f"✗ Movement registry check failed: {e}")
        return False
    
    return True

def check_frame_analyzer():
    """Check if frame analyzer can be initialized"""
    print("\nChecking frame analyzer...")
    
    try:
        from app.services.session_manager import SessionManager
        from app.storage.memory import InMemoryStorage
        from app.services.frame_analyzer import FrameAnalyzer
        
        storage = InMemoryStorage()
        session_manager = SessionManager(storage)
        analyzer = FrameAnalyzer(session_manager)
        
        print("✓ FrameAnalyzer initialized successfully")
        
    except Exception as e:
        print(f"✗ FrameAnalyzer initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all checks"""
    print("ROM Analysis API - Startup Check")
    print("=" * 50)
    
    all_good = True
    
    # Check imports
    if not check_imports():
        all_good = False
    
    # Check pose detector
    if not check_pose_detector():
        all_good = False
    
    # Check movement registry
    if not check_movement_registry():
        all_good = False
    
    # Check frame analyzer
    if not check_frame_analyzer():
        all_good = False
    
    print("\n" + "=" * 50)
    if all_good:
        print("✓ All checks passed! The API should work correctly.")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()