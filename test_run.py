"""Simple test script to verify imports and basic functionality"""
import sys
import os

print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("\nTesting imports...")

try:
    from src.ui.styles import CyberTheme
    print("✅ CyberTheme")
except Exception as e:
    print(f"❌ CyberTheme: {e}")

try:
    from src.ui.video_frame import VideoFrame
    print("✅ VideoFrame")
except Exception as e:
    print(f"❌ VideoFrame: {e}")

try:
    from src.ui.control_panel import ControlPanel
    print("✅ ControlPanel")
except Exception as e:
    print(f"❌ ControlPanel: {e}")

try:
    from src.detectors.motion_detector import MotionDetector
    print("✅ MotionDetector")
except Exception as e:
    print(f"❌ MotionDetector: {e}")

try:
    from src.detectors.noise_detector import NoiseDetector
    print("✅ NoiseDetector")
except Exception as e:
    print(f"❌ NoiseDetector: {e}")

try:
    from src.recording.video_recorder import VideoRecorder
    print("✅ VideoRecorder")
except Exception as e:
    print(f"❌ VideoRecorder: {e}")

try:
    from src.recording.audio_recorder import AudioRecorder
    print("✅ AudioRecorder")
except Exception as e:
    print(f"❌ AudioRecorder: {e}")

print("\n✅ All tests complete!")