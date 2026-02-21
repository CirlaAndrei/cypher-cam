"""Motion detection module"""
import cv2
import numpy as np
import time

class MotionDetector:
    """Handles motion detection logic with advanced features"""
    
    def __init__(self, threshold=25, min_area=500):
        self.threshold = threshold
        self.min_area = min_area
        self.first_frame = None
        self.motion_detected = False
        self.motion_count = 0
        self.motion_history = []
        self.total_motion_area = 0
        self.motion_regions = []  # Store regions where motion occurs most
        
    def detect(self, frame, show_heatmap=True):
        """Detect motion in frame with improved visualization
        
        Args:
            frame: The video frame to process
            show_heatmap: Boolean to enable/disable the purple heatmap effect
        """
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize first frame
        if self.first_frame is None:
            self.first_frame = gray
            return False, 0, frame, []
        
        # Compute difference between current and first frame
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate to fill gaps
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        total_area = 0
        motion_boxes = []
        
        # Draw motion heatmap effect (only if enabled)
        if show_heatmap:
            heatmap = cv2.applyColorMap(thresh, cv2.COLORMAP_JET)
            frame = cv2.addWeighted(frame, 0.7, heatmap, 0.3, 0)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
            
            motion_detected = True
            total_area += area
            
            # Get bounding box
            (x, y, w, h) = cv2.boundingRect(contour)
            motion_boxes.append((x, y, w, h))
            
            # Draw fancy rectangle with glow effect
            # Outer glow
            cv2.rectangle(frame, (x-2, y-2), (x + w+2, y + h+2), (0, 255, 255), 1)
            # Inner rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Corner markers for style
            corner_len = 10
            cv2.line(frame, (x, y), (x + corner_len, y), (0, 255, 0), 2)
            cv2.line(frame, (x, y), (x, y + corner_len), (0, 255, 0), 2)
            cv2.line(frame, (x + w, y), (x + w - corner_len, y), (0, 255, 0), 2)
            cv2.line(frame, (x + w, y), (x + w, y + corner_len), (0, 255, 0), 2)
            cv2.line(frame, (x, y + h), (x + corner_len, y + h), (0, 255, 0), 2)
            cv2.line(frame, (x, y + h), (x, y + h - corner_len), (0, 255, 0), 2)
            cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), (0, 255, 0), 2)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), (0, 255, 0), 2)
        
        if motion_detected:
            self.motion_count += 1
            self.motion_history.append(time.time())
            self.total_motion_area += total_area
            self.motion_regions.extend([(box[0] + box[2]//2, box[1] + box[3]//2) for box in motion_boxes])
            
            # Keep only last 1000 points for heatmap
            if len(self.motion_regions) > 1000:
                self.motion_regions = self.motion_regions[-1000:]
            
            # Draw motion heatmap points (always show these, they're not the purple overlay)
            for (cx, cy) in self.motion_regions:
                cv2.circle(frame, (cx, cy), 2, (0, 165, 255), -1)
            
            # Add stylish text with background
            text = "MOTION DETECTED"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
            cv2.rectangle(frame, (5, 5), (text_size[0] + 15, 40), (0, 0, 0), -1)
            cv2.rectangle(frame, (5, 5), (text_size[0] + 15, 40), (0, 255, 0), 1)
            cv2.putText(frame, text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Area info
            area_text = f"Area: {total_area:.0f}px"
            cv2.putText(frame, area_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Update first frame periodically
        if self.motion_count % 30 == 0:
            self.first_frame = gray
        
        return motion_detected, total_area, frame, motion_boxes
    
    def get_motion_frequency(self, seconds=60):
        """Get motion frequency over last X seconds"""
        if not self.motion_history:
            return 0
        current_time = time.time()
        recent = [t for t in self.motion_history if current_time - t <= seconds]
        return len(recent)
    
    def get_hotspots(self):
        """Get areas with most motion (for heatmap)"""
        if not self.motion_regions:
            return []
        # Cluster points to find hotspots (simplified)
        return self.motion_regions[-10:]  # Last 10 motion points