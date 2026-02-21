# test_imports.py
print("Testing imports...")

try:
    from ui.styles import CyberTheme
    print("✅ CyberTheme imported")
except Exception as e:
    print(f"❌ CyberTheme failed: {e}")

try:
    from ui.video_frame import VideoFrame
    print("✅ VideoFrame imported")
except Exception as e:
    print(f"❌ VideoFrame failed: {e}")

try:
    from detectors.motion_detector import MotionDetector
    print("✅ MotionDetector imported")
except Exception as e:
    print(f"❌ MotionDetector failed: {e}")

try:
    from utils.logger import setup_logger
    print("✅ Logger imported")
except Exception as e:
    print(f"❌ Logger failed: {e}")

print("\nTest complete!")