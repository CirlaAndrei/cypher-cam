"""Camera utilities for faster initialization"""
import cv2
import threading
import time

class CameraInitializer:
    """Handles camera initialization with timeout"""
    
    @staticmethod
    def init_camera_with_timeout(device_id=0, timeout=3):
        """Initialize camera with timeout"""
        result = [None]
        error = [None]
        
        def init():
            try:
                # Try different backends
                backends = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]
                for backend in backends:
                    try:
                        cap = cv2.VideoCapture(device_id, backend)
                        if cap.isOpened():
                            # Test read
                            ret, _ = cap.read()
                            if ret:
                                result[0] = cap
                                return
                            else:
                                cap.release()
                        else:
                            cap.release()
                    except:
                        continue
                
                # If all backends fail, try default
                cap = cv2.VideoCapture(device_id)
                if cap.isOpened():
                    result[0] = cap
                else:
                    error[0] = "Could not open camera"
            except Exception as e:
                error[0] = str(e)
        
        thread = threading.Thread(target=init)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # Timeout occurred
            return None, "Camera initialization timeout"
        
        if error[0]:
            return None, error[0]
        
        return result[0], None