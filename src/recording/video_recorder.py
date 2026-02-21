"""Video recording module for Cypher-Cam"""
import cv2
import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class VideoRecorder:
    """Handles video recording"""
    
    def __init__(self, output_dir="recordings"):
        self.output_dir = output_dir
        self.recording = False
        self.video_writer = None
        self.current_recording = None
        self.recording_start_time = None
        self.recording_reason = None
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created recordings directory: {output_dir}")
    
    def start_recording(self, frame, reason="manual"):
        """Start recording video"""
        if self.recording:
            return None
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/recording_{reason}_{timestamp}.avi"
            
            height, width = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
            
            if not self.video_writer.isOpened():
                logger.error("Failed to create video writer")
                return None
            
            self.recording = True
            self.current_recording = filename
            self.recording_start_time = time.time()
            self.recording_reason = reason
            
            logger.info(f"Started recording: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return None
    
    def stop_recording(self):
        """Stop recording video"""
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.recording = False
        if self.current_recording:
            duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            logger.info(f"Stopped recording: {self.current_recording} (Duration: {duration:.1f}s)")
            filename = self.current_recording
            self.current_recording = None
            self.recording_start_time = None
            return filename, duration
        
        return None, 0
    
    def write_frame(self, frame):
        """Write frame to video file"""
        if self.recording and self.video_writer:
            try:
                self.video_writer.write(frame)
                # Add recording indicator to frame (visual feedback)
                cv2.putText(frame, f"REC {self.recording_reason}", 
                           (frame.shape[1] - 180, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
                duration = time.time() - self.recording_start_time
                cv2.putText(frame, f"{duration:.1f}s", 
                           (frame.shape[1] - 180, 60), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            except Exception as e:
                logger.error(f"Error writing frame: {e}")