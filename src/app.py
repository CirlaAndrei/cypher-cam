"""Main application class (simplified)"""
import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import threading
import time
import os
from datetime import datetime

# Import our modules
from ui.styles import CyberTheme
from ui.video_frame import VideoFrame
from ui.control_panel import ControlPanel
from detectors.motion_detector import MotionDetector
from detectors.noise_detector import NoiseDetector
from recording.video_recorder import VideoRecorder
from recording.audio_recorder import AudioRecorder
from utils.logger import setup_logger

class CypherCam:
    """Main application class"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cypher-Cam Surveillance System")
        self.root.geometry("1300x800")
        
        # Apply cyber theme
        self.theme = CyberTheme()
        self.theme.apply_theme(root)
        
        # Initialize components
        self.setup_components()
        self.setup_ui()
        
        self.logger.info("Cypher-Cam initialized")
    
    def setup_components(self):
        """Initialize all sub-components"""
        self.logger = setup_logger()
        
        # Detectors
        self.motion_detector = MotionDetector(threshold=25, min_area=500)
        self.noise_detector = NoiseDetector(threshold=0.1)
        
        # Recorders
        self.video_recorder = VideoRecorder()
        self.audio_recorder = AudioRecorder()
        
        # State
        self.is_running = False
        self.cap = None
        self.current_frame = None
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Event tracking
        self.motion_events = 0
        self.noise_events = 0
        self.last_motion_time = None
        self.last_noise_time = None
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video frame (left side)
        self.video_frame = VideoFrame(main_frame, self, style=self.theme)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control panel (right side)
        self.control_panel = ControlPanel(main_frame, self, style=self.theme)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    
    def toggle_camera(self):
        """Start or stop camera"""
        if not self.is_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start camera and detectors"""
        try:
            # Start camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Could not open camera")
                return
            
            # Start noise detector
            try:
                self.noise_detector.start_listening()
            except Exception as e:
                self.logger.warning(f"Noise detector unavailable: {e}")
            
            self.is_running = True
            self.start_time = time.time()
            self.control_panel.update_status("Camera Running")
            
            # Start processing thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            self.logger.info("Camera started")
            self.add_event("System started")
            
        except Exception as e:
            self.logger.error(f"Start error: {e}")
            messagebox.showerror("Error", str(e))
    
    def stop_camera(self):
        """Stop camera and detectors"""
        self.is_running = False
        
        # Stop recording
        if self.video_recorder.recording:
            self.video_recorder.stop_recording()
            self.audio_recorder.stop_recording()
        
        # Stop detectors
        if hasattr(self, 'noise_detector'):
            self.noise_detector.stop_listening()
        
        if self.cap:
            self.cap.release()
        
        self.control_panel.update_status("Ready")
        self.control_panel.update_recording_button(reset=True)
        
        self.logger.info("Camera stopped")
        self.add_event("System stopped")
    
    def process_video(self):
        """Main video processing loop"""
        self.last_time = time.time()
        self.frame_count = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            self.current_frame = frame.copy()
            
            # Calculate FPS
            self.frame_count += 1
            current_time = time.time()
            if current_time - self.last_time >= 1.0:
                self.fps = self.frame_count
                self.frame_count = 0
                self.last_time = current_time
                self.control_panel.update_fps(self.fps)
            
            # Detect motion
            motion, area, processed_frame, boxes = self.motion_detector.detect(frame)
            
            if motion:
                self.motion_events += 1
                self.last_motion_time = time.time()
                self.control_panel.update_motion_status(True)
                self.video_frame.update_indicators(motion=True)
                
                # Handle recording
                self.handle_event_recording("motion", processed_frame)
            else:
                self.control_panel.update_motion_status(False)
                self.video_frame.update_indicators(motion=False)
            
            # Detect noise
            if self.noise_detector:
                noise_level = self.noise_detector.get_current_noise_level()
                noise_detected = self.noise_detector.noise_detected
                
                self.control_panel.update_noise_level(noise_level)
                
                if noise_detected:
                    self.noise_events += 1
                    self.last_noise_time = time.time()
                    self.control_panel.update_noise_status(True)
                    self.video_frame.update_indicators(noise=True)
                    
                    # Handle recording
                    self.handle_event_recording("noise", processed_frame)
                else:
                    self.control_panel.update_noise_status(False)
                    self.video_frame.update_indicators(noise=False)
            
            # Handle recording stop
            self.check_recording_timeout()
            
            # Write frame if recording
            if self.video_recorder.recording:
                self.video_recorder.write_frame(processed_frame)
                self.video_frame.update_indicators(recording=True)
                
                # Add audio if recording
                if self.audio_recorder.recording and self.noise_detector:
                    if not self.noise_detector.audio_queue.empty():
                        audio_data, _ = self.noise_detector.audio_queue.get()
                        self.audio_recorder.add_frame(audio_data)
            else:
                self.video_frame.update_indicators(recording=False)
            
            # Update display
            frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            self.video_frame.update_display(frame_rgb)
            
            # Update stats
            self.control_panel.update_stats(
                motion_events=self.motion_events,
                noise_events=self.noise_events,
                uptime=time.time() - self.start_time
            )
    
    def handle_event_recording(self, event_type, frame):
        """Handle recording triggered by events"""
        if (self.control_panel.get_setting(f'record_on_{event_type}') and 
            not self.video_recorder.recording and 
            not self.control_panel.get_setting('auto_record')):
            
            self.video_recorder.start_recording(frame, reason=event_type)
            self.audio_recorder.start_recording()
            self.add_event(f"{event_type.capitalize()} detected - Recording started")
    
    def check_recording_timeout(self):
        """Check if recording should stop due to inactivity"""
        if (not self.control_panel.get_setting('auto_record') and 
            self.video_recorder.recording):
            
            time_since_motion = time.time() - (self.last_motion_time or 0)
            time_since_noise = time.time() - (self.last_noise_time or 0)
            timeout = self.control_panel.get_setting('recording_duration')
            
            if time_since_motion > timeout and time_since_noise > timeout:
                video_file, duration = self.video_recorder.stop_recording()
                audio_file = self.audio_recorder.stop_recording()
                if video_file:
                    self.add_event(f"Recording stopped - Duration: {duration:.1f}s")
    
    def toggle_manual_recording(self):
        """Toggle manual recording"""
        if not self.video_recorder.recording:
            if self.current_frame is not None:
                self.video_recorder.start_recording(self.current_frame, reason="manual")
                self.audio_recorder.start_recording()
                self.control_panel.update_recording_button(recording=True)
                self.add_event("Started manual recording")
        else:
            video_file, duration = self.video_recorder.stop_recording()
            audio_file = self.audio_recorder.stop_recording()
            self.control_panel.update_recording_button(recording=False)
            if video_file:
                self.add_event(f"Stopped manual recording - Duration: {duration:.1f}s")
    
    def take_snapshot(self):
        """Take a snapshot"""
        if self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recordings/snapshot_{timestamp}.jpg"
            cv2.imwrite(filename, cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))
            self.add_event(f"Snapshot saved")
    
    def add_event(self, event_text):
        """Add event to log"""
        self.control_panel.add_event(event_text)

def main():
    root = tk.Tk()
    app = CypherCam(root)
    
    def on_closing():
        if app.is_running:
            app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()