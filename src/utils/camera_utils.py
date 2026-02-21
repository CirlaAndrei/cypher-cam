"""Camera utilities for faster initialization"""
import cv2
import threading
import time
import logging

logger = logging.getLogger(__name__)

class CameraInitializer:
    """Handles camera initialization with timeout"""
    
    @staticmethod
    def init_camera_with_timeout(device_id=0, timeout=5):
        """Initialize camera with timeout (increased to 5 seconds)"""
        result = [None]
        error = [None]
        
        def init():
            try:
                # Try different backends in order of reliability on Windows
                backends = [
                    cv2.CAP_DSHOW,      # DirectShow (fastest on Windows)
                    cv2.CAP_MSMF,        # Microsoft Media Foundation
                    cv2.CAP_ANY          # Let OpenCV decide
                ]
                
                for backend in backends:
                    try:
                        logger.info(f"Trying camera backend: {backend}")
                        cap = cv2.VideoCapture(device_id, backend)
                        
                        if cap.isOpened():
                            # Test read with retry
                            for attempt in range(3):
                                ret, frame = cap.read()
                                if ret and frame is not None and frame.size > 0:
                                    logger.info(f"Camera opened successfully with backend {backend}")
                                    result[0] = cap
                                    return
                                time.sleep(0.1)
                            
                            # If test reads fail, release and try next backend
                            cap.release()
                        else:
                            cap.release()
                    except Exception as e:
                        logger.warning(f"Backend {backend} failed: {e}")
                        continue
                
                # If all backends fail, try one last time with default
                logger.info("Trying default camera backend")
                cap = cv2.VideoCapture(device_id)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        result[0] = cap
                        return
                    else:
                        cap.release()
                
                error[0] = "Could not open camera - no working backend found"
                
            except Exception as e:
                error[0] = str(e)
        
        thread = threading.Thread(target=init)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # Timeout occurred
            logger.error(f"Camera initialization timeout after {timeout} seconds")
            return None, f"Camera initialization timeout. Try:\n1. Check if another app is using the camera\n2. Restart your computer\n3. Update camera drivers"
        
        if error[0]:
            logger.error(f"Camera error: {error[0]}")
            return None, error[0]
        
        if result[0] is None:
            return None, "Unknown error initializing camera"
        
        return result[0], None
    
    @staticmethod
    def test_camera_device(device_id=0):
        """Quick test to see if camera is accessible"""
        try:
            cap = cv2.VideoCapture(device_id, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    return True, "Camera working"
                return False, "Camera opened but cannot read frames"
            return False, "Cannot open camera"
        except Exception as e:
            return False, str(e)