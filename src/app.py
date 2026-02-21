"""Main application class for Cypher-Cam"""
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
from detectors.object_detector import ObjectDetector
from recording.video_recorder import VideoRecorder
from recording.audio_recorder import AudioRecorder
from utils.logger import setup_logger
from utils.camera_utils import CameraInitializer
from web_server import WebServer

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
        
        # Start web server
        try:
            self.web_server = WebServer(self)
            self.web_server.start()
        except Exception as e:
            self.logger.error(f"Failed to start web server: {e}")
        
        self.logger.info("Cypher-Cam initialized")
    
    def setup_components(self):
        """Initialize all sub-components"""
        self.logger = setup_logger()
        
        # Detectors
        self.motion_detector = MotionDetector(threshold=25, min_area=500)
        self.noise_detector = NoiseDetector(threshold=0.1)
        self.object_detector = ObjectDetector(confidence_threshold=0.5)
        
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
        
        # Object detection
        self.people_count = 0
        self.detected_objects = []
        self.show_heatmap = True  # Toggle for heatmap effect
        
        # Performance settings
        self.frame_skip = 2  # Process every 2nd frame
        self.object_detection_interval = 10  # Run object detection every 10 frames
        self.frame_counter = 0
    
    def setup_ui(self):
        """Setup the main UI layout"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Video frame (left side) - NO style parameter
        self.video_frame = VideoFrame(main_frame, self)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Control panel (right side) - NO style parameter
        self.control_panel = ControlPanel(main_frame, self)
        self.control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
    
    def toggle_camera(self):
        """Start or stop camera"""
        if not self.is_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Start camera and detectors with improved performance and error handling"""
        try:
            # Show loading status
            self.control_panel.update_status("Initializing Camera...")
            self.root.update()  # Force UI update
            
            # First, test if camera is accessible
            working, message = CameraInitializer.test_camera_device(0)
            if not working:
                self.logger.warning(f"Camera test: {message}")
                # Ask user if they want to continue trying
                response = messagebox.askyesno(
                    "Camera Warning",
                    f"Camera test returned: {message}\n\n"
                    "Do you want to try initializing anyway?"
                )
                if not response:
                    self.control_panel.update_status("Ready")
                    return
            
            # Use camera initializer with increased timeout (5 seconds)
            cap, error = CameraInitializer.init_camera_with_timeout(0, timeout=5)
            
            if error:
                self.logger.error(f"Camera error: {error}")
                # Show more helpful error message
                messagebox.showerror(
                    "Camera Error", 
                    f"Could not initialize camera:\n\n{error}\n\n"
                    "Troubleshooting tips:\n"
                    "1. Make sure no other app is using the camera\n"
                    "2. Try restarting your computer\n"
                    "3. Check Windows Camera privacy settings\n"
                    "   (Settings → Privacy & Security → Camera)\n"
                    "4. Update your camera drivers\n"
                    "5. If using a laptop, check if there's a physical camera switch"
                )
                self.control_panel.update_status("Ready")
                return
            
            if not cap:
                messagebox.showerror("Error", "Could not open camera - unknown error")
                self.control_panel.update_status("Ready")
                return
            
            self.cap = cap
            
            # Set optimal properties for performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer size
            self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus for speed
            
            # Try to disable auto exposure for faster startup
            try:
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
            except:
                pass
            
            # Start noise detector in background
            try:
                noise_thread = threading.Thread(target=self.noise_detector.start_listening)
                noise_thread.daemon = True
                noise_thread.start()
            except Exception as e:
                self.logger.warning(f"Noise detector unavailable: {e}")
            
            self.is_running = True
            self.start_time = time.time()
            self.frame_counter = 0
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            # Update UI
            self.control_panel.update_status("Camera Running")
            self.add_event("System started")
            self.logger.info("Camera started successfully")
            
        except Exception as e:
            self.logger.error(f"Start error: {e}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            self.control_panel.update_status("Ready")
    
    def stop_camera(self):
        """Stop camera and detectors"""
        self.is_running = False
        
        # Stop recording
        if self.video_recorder.recording:
            self.video_recorder.stop_recording()
            self.audio_recorder.stop_recording()
        
        # Stop detectors
        if hasattr(self, 'noise_detector'):
            try:
                self.noise_detector.stop_listening()
            except:
                pass
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.control_panel.update_status("Ready")
        self.control_panel.update_recording_button(reset=True)
        
        self.logger.info("Camera stopped")
        self.add_event("System stopped")
    
    def process_video(self):
        """Main video processing loop with performance optimizations"""
        self.last_time = time.time()
        self.frame_count = 0
        error_count = 0
        
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    error_count += 1
                    if error_count > 30:  # If we get 30 consecutive errors, stop
                        self.logger.error("Too many frame read errors, stopping camera")
                        self.root.after(0, self.stop_camera)
                        break
                    time.sleep(0.1)  # Prevent CPU spinning
                    continue
                
                error_count = 0  # Reset error count on successful read
                self.frame_counter += 1
                self.current_frame = frame.copy()
                
                # Calculate FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_time = current_time
                    self.control_panel.update_fps(self.fps)
                    self.video_frame.update_fps(self.fps)
                
                # Process frame (with frame skipping for performance)
                if self.frame_counter % self.frame_skip == 0:
                    # Detect motion (always do this for security)
                    motion, area, processed_frame, boxes = self.motion_detector.detect(
                        frame, show_heatmap=self.show_heatmap
                    )
                    
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
                    
                    # Object detection (run less frequently to save CPU)
                    if self.frame_counter % (self.frame_skip * self.object_detection_interval) == 0:
                        try:
                            objects, processed_frame = self.object_detector.detect(processed_frame)
                            self.detected_objects = objects
                            self.people_count = self.object_detector.count_people(objects)
                            
                            # Draw people count on frame
                            cv2.putText(processed_frame, f"People: {self.people_count}", 
                                       (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            
                            # Draw object count
                            cv2.putText(processed_frame, f"Objects: {len(objects)}", 
                                       (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                            
                        except Exception as e:
                            self.logger.error(f"Object detection error: {e}")
                            processed_frame = frame.copy()
                else:
                    # Skip heavy processing, just pass the frame
                    processed_frame = frame.copy()
                
                # Detect noise (lightweight, run every frame)
                if self.noise_detector and hasattr(self.noise_detector, 'is_listening') and self.noise_detector.is_listening:
                    try:
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
                    except:
                        pass
                
                # Handle recording stop
                self.check_recording_timeout()
                
                # Write frame if recording
                if self.video_recorder.recording:
                    self.video_recorder.write_frame(processed_frame)
                    self.video_frame.update_indicators(recording=True)
                    
                    # Add audio if recording (lightweight)
                    if self.audio_recorder.recording and self.noise_detector:
                        try:
                            if not self.noise_detector.audio_queue.empty():
                                audio_data, _ = self.noise_detector.audio_queue.get_nowait()
                                self.audio_recorder.add_frame(audio_data)
                        except:
                            pass
                else:
                    self.video_frame.update_indicators(recording=False)
                
                # Add timestamp to frame
                cv2.putText(processed_frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                           (10, processed_frame.shape[0] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Update display
                try:
                    frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                    self.video_frame.update_display(frame_rgb)
                except:
                    pass
                
                # Update stats (every 30 frames to reduce UI updates)
                if self.frame_counter % 30 == 0:
                    self.control_panel.update_stats(
                        motion_events=self.motion_events,
                        noise_events=self.noise_events,
                        uptime=time.time() - self.start_time,
                        people_count=self.people_count,
                        objects_count=len(self.detected_objects)
                    )
                
                # Small sleep to prevent CPU overload
                time.sleep(0.01)
                
            except Exception as e:
                self.logger.error(f"Error in video processing loop: {e}")
                time.sleep(0.1)
    
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
    
    def toggle_heatmap(self, enabled):
        """Toggle heatmap display"""
        self.show_heatmap = enabled
        self.add_event(f"Heatmap {'enabled' if enabled else 'disabled'}")

def main():
    """Main entry point"""
    print("\n" + "="*50)
    print("🔒 Cypher-Cam Surveillance System")
    print("="*50)
    print("📱 Web interface: http://localhost:5000")
    print("📹 Local app running...")
    print("="*50 + "\n")
    
    root = tk.Tk()
    app = CypherCam(root)
    
    def on_closing():
        if app.is_running:
            app.stop_camera()
        # Stop web server
        if hasattr(app, 'web_server'):
            app.web_server.stop()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()