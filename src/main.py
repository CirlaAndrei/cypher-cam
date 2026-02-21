"""
Cypher-Cam Surveillance System
Main entry point for the application
"""

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import logging
import os
import sys
from datetime import datetime
import pygame  # For sound alerts
import sounddevice as sd
import numpy as np
import wave
import scipy.io.wavfile as wav
import queue
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cypher-cam.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NoiseDetector:
    """Handles noise/sound detection"""
    
    def __init__(self, threshold=0.1, sample_rate=44100, duration=0.1):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.duration = duration
        self.noise_detected = False
        self.noise_count = 0
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
    def start_listening(self):
        """Start audio stream for noise detection"""
        self.is_listening = True
        self.audio_stream = sd.InputStream(
            callback=self.audio_callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=int(self.sample_rate * self.duration)
        )
        self.audio_stream.start()
        logger.info("Noise detector started")
        
    def stop_listening(self):
        """Stop audio stream"""
        self.is_listening = False
        if hasattr(self, 'audio_stream'):
            self.audio_stream.stop()
            self.audio_stream.close()
        logger.info("Noise detector stopped")
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            logger.warning(f"Audio status: {status}")
        
        # Calculate volume level (RMS)
        volume_norm = np.linalg.norm(indata) * 10
        
        # Check if volume exceeds threshold
        if volume_norm > self.threshold:
            self.noise_detected = True
            self.noise_count += 1
        else:
            self.noise_detected = False
        
        # Put data in queue for potential recording
        self.audio_queue.put((indata.copy(), volume_norm))
    
    def get_current_noise_level(self):
        """Get current noise level from queue"""
        if not self.audio_queue.empty():
            _, volume = self.audio_queue.get()
            return volume
        return 0

class MotionDetector:
    """Handles motion detection logic"""
    
    def __init__(self, threshold=25, min_area=500):
        self.threshold = threshold
        self.min_area = min_area
        self.first_frame = None
        self.motion_detected = False
        self.motion_count = 0
        self.motion_history = []  # Store recent motion events
        
    def detect(self, frame):
        """Detect motion in frame"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Initialize first frame
        if self.first_frame is None:
            self.first_frame = gray
            return False, 0, frame
        
        # Compute difference between current and first frame
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Dilate to fill gaps
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        total_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_area:
                continue
            
            motion_detected = True
            total_area += area
            
            # Draw rectangle around motion
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        if motion_detected:
            self.motion_count += 1
            self.motion_history.append(time.time())
            # Keep only last 100 events
            if len(self.motion_history) > 100:
                self.motion_history.pop(0)
            
            cv2.putText(frame, "MOTION DETECTED", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(frame, f"Area: {total_area:.0f}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Update first frame periodically
        if self.motion_count % 30 == 0:
            self.first_frame = gray
        
        return motion_detected, total_area, frame
    
    def get_motion_frequency(self, seconds=60):
        """Get motion frequency over last X seconds"""
        if not self.motion_history:
            return 0
        current_time = time.time()
        recent = [t for t in self.motion_history if current_time - t <= seconds]
        return len(recent)

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
    
    def start_recording(self, frame, reason="manual"):
        """Start recording video"""
        if self.recording:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/recording_{reason}_{timestamp}.avi"
        
        height, width = frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (width, height))
        self.recording = True
        self.current_recording = filename
        self.recording_start_time = time.time()
        self.recording_reason = reason
        
        logger.info(f"Started recording: {filename}")
        return filename
    
    def stop_recording(self):
        """Stop recording video"""
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.recording = False
        if self.current_recording:
            logger.info(f"Stopped recording: {self.current_recording}")
            filename = self.current_recording
            duration = time.time() - self.recording_start_time if self.recording_start_time else 0
            self.current_recording = None
            self.recording_start_time = None
            return filename, duration
        
        return None, 0
    
    def write_frame(self, frame):
        """Write frame to video file"""
        if self.recording and self.video_writer:
            self.video_writer.write(frame)
            # Add recording indicator to frame
            cv2.putText(frame, f"REC {self.recording_reason}", 
                       (frame.shape[1] - 150, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Duration: {int(time.time() - self.recording_start_time)}s", 
                       (frame.shape[1] - 150, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

class SoundRecorder:
    """Handles sound recording separately"""
    
    def __init__(self, output_dir="recordings"):
        self.output_dir = output_dir
        self.recording = False
        self.frames = []
        self.sample_rate = 44100
        
    def start_recording(self):
        """Start recording sound"""
        self.recording = True
        self.frames = []
        
    def stop_recording(self):
        """Stop recording and save file"""
        self.recording = False
        if self.frames:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.output_dir}/audio_{timestamp}.wav"
            
            # Save audio file
            audio_data = np.concatenate(self.frames, axis=0)
            wav.write(filename, self.sample_rate, audio_data.astype(np.int16))
            
            return filename
        return None
    
    def add_frame(self, audio_data):
        """Add audio frame to recording"""
        if self.recording:
            self.frames.append(audio_data.copy())

class CypherCam:
    """Main application class for Cypher-Cam Surveillance System"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cypher-Cam Surveillance System")
        self.root.geometry("1200x800")
        
        # Set dark mode colors
        self.bg_color = '#1e1e1e'
        self.fg_color = '#ffffff'
        self.accent_color = '#007acc'
        self.alert_color = '#ff4444'
        self.success_color = '#4CAF50'
        
        self.root.configure(bg=self.bg_color)
        
        # Video capture
        self.cap = None
        self.is_running = False
        self.current_frame = None
        
        # Motion detection
        self.motion_detector = MotionDetector(threshold=25, min_area=500)
        self.motion_threshold = 25
        self.min_area = 500
        self.motion_events = 0
        self.last_motion_time = None
        
        # Noise detection
        self.noise_detector = None
        self.noise_threshold = 0.1
        self.noise_events = 0
        self.last_noise_time = None
        self.current_noise_level = 0
        
        # Recording
        self.video_recorder = VideoRecorder()
        self.sound_recorder = SoundRecorder()
        self.auto_record = False
        self.record_on_motion = True
        self.record_on_noise = True
        self.recording_duration = 10  # seconds after event stops
        
        # Audio alert
        self.alert_enabled = True
        pygame.mixer.init()
        
        # Statistics
        self.fps = 0
        self.frame_count = 0
        self.last_time = time.time()
        self.start_time = time.time()
        
        # Initialize UI
        self.setup_ui()
        
        logger.info("Cypher-Cam initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style configuration for dark mode
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.accent_color, foreground=self.fg_color)
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe', background=self.bg_color, foreground=self.fg_color)
        style.configure('TLabelframe.Label', background=self.bg_color, foreground=self.fg_color)
        style.configure('Red.TButton', background=self.alert_color, foreground=self.fg_color)
        style.configure('Green.TButton', background=self.success_color, foreground=self.fg_color)
        
        # Video feed frame (left side)
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Noise level indicator (below video)
        noise_frame = ttk.Frame(video_frame)
        noise_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(noise_frame, text="Noise Level:").pack(side=tk.LEFT)
        self.noise_bar = ttk.Progressbar(
            noise_frame, 
            length=200, 
            mode='determinate',
            style="red.Horizontal.TProgressbar"
        )
        self.noise_bar.pack(side=tk.LEFT, padx=5)
        self.noise_value_label = ttk.Label(noise_frame, text="0.00")
        self.noise_value_label.pack(side=tk.LEFT)
        
        # Control panel (right side)
        control_frame = ttk.Frame(main_frame, width=350)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        control_frame.pack_propagate(False)
        
        # Create canvas with scrollbar for control panel
        canvas = tk.Canvas(control_frame, bg=self.bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Title
        title_label = ttk.Label(
            scrollable_frame, 
            text="Cypher-Cam Controls",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Camera controls section
        camera_frame = ttk.LabelFrame(scrollable_frame, text="Camera Control")
        camera_frame.pack(fill=tk.X, pady=5)
        
        self.start_button = ttk.Button(
            camera_frame,
            text="Start Camera",
            command=self.toggle_camera
        )
        self.start_button.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_label = ttk.Label(
            camera_frame,
            text="Status: Ready",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=5)
        
        # Motion detection settings
        motion_frame = ttk.LabelFrame(scrollable_frame, text="Motion Detection")
        motion_frame.pack(fill=tk.X, pady=5)
        
        # Threshold slider
        ttk.Label(motion_frame, text="Sensitivity:").pack(pady=2)
        self.threshold_var = tk.IntVar(value=25)
        threshold_scale = ttk.Scale(
            motion_frame, 
            from_=5, to=50, 
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.update_threshold
        )
        threshold_scale.pack(fill=tk.X, padx=5, pady=2)
        
        self.threshold_label = ttk.Label(motion_frame, text="Threshold: 25")
        self.threshold_label.pack()
        
        # Min area slider
        ttk.Label(motion_frame, text="Min Area:").pack(pady=2)
        self.area_var = tk.IntVar(value=500)
        area_scale = ttk.Scale(
            motion_frame, 
            from_=100, to=2000, 
            orient=tk.HORIZONTAL,
            variable=self.area_var,
            command=self.update_area
        )
        area_scale.pack(fill=tk.X, padx=5, pady=2)
        
        self.area_label = ttk.Label(motion_frame, text="Min Area: 500")
        self.area_label.pack()
        
        # Noise detection settings
        noise_settings_frame = ttk.LabelFrame(scrollable_frame, text="Noise Detection")
        noise_settings_frame.pack(fill=tk.X, pady=5)
        
        # Noise threshold slider
        ttk.Label(noise_settings_frame, text="Noise Sensitivity:").pack(pady=2)
        self.noise_threshold_var = tk.DoubleVar(value=0.1)
        noise_scale = ttk.Scale(
            noise_settings_frame, 
            from_=0.01, to=0.5, 
            orient=tk.HORIZONTAL,
            variable=self.noise_threshold_var,
            command=self.update_noise_threshold
        )
        noise_scale.pack(fill=tk.X, padx=5, pady=2)
        
        self.noise_threshold_label = ttk.Label(noise_settings_frame, text="Noise Threshold: 0.10")
        self.noise_threshold_label.pack()
        
        # Current noise level
        self.current_noise_label = ttk.Label(noise_settings_frame, text="Current: 0.00")
        self.current_noise_label.pack()
        
        # Recording settings
        record_frame = ttk.LabelFrame(scrollable_frame, text="Recording")
        record_frame.pack(fill=tk.X, pady=5)
        
        self.record_on_motion_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            record_frame, 
            text="Record on Motion",
            variable=self.record_on_motion_var,
            command=self.toggle_record_on_motion
        ).pack(pady=2)
        
        self.record_on_noise_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            record_frame, 
            text="Record on Noise",
            variable=self.record_on_noise_var,
            command=self.toggle_record_on_noise
        ).pack(pady=2)
        
        self.auto_record_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            record_frame, 
            text="Continuous Recording",
            variable=self.auto_record_var,
            command=self.toggle_auto_record
        ).pack(pady=2)
        
        self.alert_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            record_frame, 
            text="Sound Alerts",
            variable=self.alert_var,
            command=self.toggle_alerts
        ).pack(pady=2)
        
        # Manual recording button
        button_frame = ttk.Frame(record_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.manual_record_button = ttk.Button(
            button_frame,
            text="Start Manual Recording",
            command=self.toggle_manual_recording,
            style='Green.TButton'
        )
        self.manual_record_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Snapshot button
        self.snapshot_button = ttk.Button(
            button_frame,
            text="📸",
            command=self.take_snapshot,
            width=3
        )
        self.snapshot_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Statistics section
        stats_frame = ttk.LabelFrame(scrollable_frame, text="Live Statistics")
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Create grid for stats
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Row 1
        ttk.Label(stats_grid, text="Motion Events:", font=('Arial', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.motion_label = ttk.Label(stats_grid, text="0")
        self.motion_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_grid, text="Noise Events:", font=('Arial', 9, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(10,0))
        self.noise_label = ttk.Label(stats_grid, text="0")
        self.noise_label.grid(row=0, column=3, sticky=tk.W, pady=2)
        
        # Row 2
        ttk.Label(stats_grid, text="Motion Status:", font=('Arial', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.motion_status_label = ttk.Label(stats_grid, text="None")
        self.motion_status_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_grid, text="Noise Status:", font=('Arial', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=2, padx=(10,0))
        self.noise_status_label = ttk.Label(stats_grid, text="None")
        self.noise_status_label.grid(row=1, column=3, sticky=tk.W, pady=2)
        
        # Row 3
        ttk.Label(stats_grid, text="Recording:", font=('Arial', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.recording_label = ttk.Label(stats_grid, text="No")
        self.recording_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(stats_grid, text="FPS:", font=('Arial', 9, 'bold')).grid(row=2, column=2, sticky=tk.W, pady=2, padx=(10,0))
        self.fps_label = ttk.Label(stats_grid, text="0")
        self.fps_label.grid(row=2, column=3, sticky=tk.W, pady=2)
        
        # Row 4
        ttk.Label(stats_grid, text="Uptime:", font=('Arial', 9, 'bold')).grid(row=3, column=0, sticky=tk.W, pady=2)
        self.uptime_label = ttk.Label(stats_grid, text="00:00:00")
        self.uptime_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Recent events
        events_frame = ttk.LabelFrame(scrollable_frame, text="Recent Events")
        events_frame.pack(fill=tk.X, pady=10)
        
        # Create listbox with scrollbar
        listbox_frame = ttk.Frame(events_frame)
        listbox_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.events_listbox = tk.Listbox(
            listbox_frame, 
            height=8,
            bg=self.bg_color,
            fg=self.fg_color,
            selectbackground=self.accent_color,
            font=('Consolas', 8)
        )
        self.events_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        events_scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.events_listbox.yview)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_listbox.configure(yscrollcommand=events_scrollbar.set)
        
        # Clear events button
        ttk.Button(
            events_frame,
            text="Clear Events",
            command=self.clear_events
        ).pack(pady=5)
        
        logger.info("UI setup complete")
    
    def update_threshold(self, value):
        """Update motion detection threshold"""
        self.motion_threshold = int(float(value))
        self.threshold_label.config(text=f"Threshold: {self.motion_threshold}")
        self.motion_detector.threshold = self.motion_threshold
    
    def update_area(self, value):
        """Update minimum area for motion detection"""
        self.min_area = int(float(value))
        self.area_label.config(text=f"Min Area: {self.min_area}")
        self.motion_detector.min_area = self.min_area
    
    def update_noise_threshold(self, value):
        """Update noise detection threshold"""
        self.noise_threshold = float(value)
        self.noise_threshold_label.config(text=f"Noise Threshold: {self.noise_threshold:.2f}")
        if self.noise_detector:
            self.noise_detector.threshold = self.noise_threshold
    
    def toggle_record_on_motion(self):
        """Toggle recording on motion detection"""
        self.record_on_motion = self.record_on_motion_var.get()
        logger.info(f"Record on motion: {self.record_on_motion}")
    
    def toggle_record_on_noise(self):
        """Toggle recording on noise detection"""
        self.record_on_noise = self.record_on_noise_var.get()
        logger.info(f"Record on noise: {self.record_on_noise}")
    
    def toggle_auto_record(self):
        """Toggle continuous recording"""
        self.auto_record = self.auto_record_var.get()
        if self.auto_record and self.is_running and self.current_frame is not None:
            self.video_recorder.start_recording(self.current_frame, reason="continuous")
            self.sound_recorder.start_recording()
        elif not self.auto_record and self.video_recorder.recording:
            self.video_recorder.stop_recording()
            self.sound_recorder.stop_recording()
        logger.info(f"Auto record: {self.auto_record}")
    
    def toggle_alerts(self):
        """Toggle sound alerts"""
        self.alert_enabled = self.alert_var.get()
        logger.info(f"Sound alerts: {self.alert_enabled}")
    
    def toggle_manual_recording(self):
        """Toggle manual recording"""
        if not self.video_recorder.recording:
            if self.current_frame is not None:
                filename = self.video_recorder.start_recording(self.current_frame, reason="manual")
                self.sound_recorder.start_recording()
                self.manual_record_button.config(text="Stop Manual Recording", style='Red.TButton')
                self.recording_label.config(text="Recording: Yes (Manual)")
                self.add_event(f"Started manual recording")
        else:
            video_file, duration = self.video_recorder.stop_recording()
            audio_file = self.sound_recorder.stop_recording()
            self.manual_record_button.config(text="Start Manual Recording", style='Green.TButton')
            self.recording_label.config(text="Recording: No")
            if video_file:
                self.add_event(f"Stopped recording - Duration: {duration:.1f}s")
    
    def take_snapshot(self):
        """Take a snapshot of current frame"""
        if self.current_frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recordings/snapshot_{timestamp}.jpg"
            cv2.imwrite(filename, cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))
            self.add_event(f"Snapshot saved: {os.path.basename(filename)}")
            logger.info(f"Snapshot saved: {filename}")
    
    def add_event(self, event_text):
        """Add event to listbox"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.events_listbox.insert(0, f"[{timestamp}] {event_text}")
        # Keep only last 20 events
        while self.events_listbox.size() > 20:
            self.events_listbox.delete(20)
    
    def clear_events(self):
        """Clear all events from listbox"""
        self.events_listbox.delete(0, tk.END)
    
    def toggle_camera(self):
        """Start or stop the camera"""
        if not self.is_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """Initialize and start the camera and noise detector"""
        try:
            # Start camera
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("Could not open camera")
                messagebox.showerror("Error", "Could not open camera")
                return
            
            # Start noise detector
            try:
                self.noise_detector = NoiseDetector(threshold=self.noise_threshold)
                self.noise_detector.start_listening()
            except Exception as e:
                logger.warning(f"Could not start noise detector: {e}")
                self.noise_detector = None
            
            self.is_running = True
            self.start_time = time.time()
            self.start_button.config(text="Stop Camera")
            self.status_label.config(text="Status: Camera Running")
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            logger.info("Camera started")
            self.add_event("System started - Camera and noise detection active")
            
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
            messagebox.showerror("Error", f"Could not start camera: {e}")
    
    def stop_camera(self):
        """Stop the camera and noise detector"""
        self.is_running = False
        
        # Stop recording if active
        if self.video_recorder.recording:
            self.video_recorder.stop_recording()
            self.sound_recorder.stop_recording()
        
        # Stop noise detector
        if self.noise_detector:
            self.noise_detector.stop_listening()
        
        if self.cap:
            self.cap.release()
        
        self.start_button.config(text="Start Camera")
        self.status_label.config(text="Status: Ready")
        self.manual_record_button.config(text="Start Manual Recording", style='Green.TButton')
        
        logger.info("Camera stopped")
        self.add_event("System stopped")
    
    def process_video(self):
        """Main video processing loop"""
        self.last_time = time.time()
        self.frame_count = 0
        motion_cooldown = 0
        noise_cooldown = 0
        
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame.copy()
                
                # Calculate FPS
                self.frame_count += 1
                current_time = time.time()
                if current_time - self.last_time >= 1.0:
                    self.fps = self.frame_count
                    self.frame_count = 0
                    self.last_time = current_time
                
                # Detect motion
                motion_detected, area, processed_frame = self.motion_detector.detect(frame)
                
                if motion_detected and motion_cooldown <= 0:
                    self.motion_events += 1
                    self.last_motion_time = time.time()
                    
                    # Update motion status
                    self.motion_status_label.config(
                        text="ACTIVE",
                        foreground=self.alert_color
                    )
                    
                    # Add timestamp to frame
                    cv2.putText(processed_frame, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                               (10, processed_frame.shape[0] - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Start recording if enabled
                    if (self.record_on_motion and not self.video_recorder.recording 
                        and not self.auto_record):
                        filename = self.video_recorder.start_recording(processed_frame, reason="motion")
                        self.sound_recorder.start_recording()
                        self.add_event(f"Motion detected - Recording started")
                    
                    # Play sound alert
                    if self.alert_enabled:
                        self.root.bell()
                    
                    motion_cooldown = 10  # Cooldown frames
                else:
                    if motion_cooldown > 0:
                        motion_cooldown -= 1
                    
                    # Update motion status
                    if time.time() - (self.last_motion_time or 0) < 1:
                        self.motion_status_label.config(
                            text="ACTIVE",
                            foreground=self.alert_color
                        )
                    else:
                        self.motion_status_label.config(
                            text="None",
                            foreground=self.fg_color
                        )
                
                # Get noise level
                if self.noise_detector:
                    self.current_noise_level = self.noise_detector.get_current_noise_level()
                    noise_detected = self.noise_detector.noise_detected
                    
                    # Update noise bar
                    noise_percent = min(100, (self.current_noise_level / 0.5) * 100)
                    self.noise_bar['value'] = noise_percent
                    self.noise_value_label.config(text=f"{self.current_noise_level:.3f}")
                    self.current_noise_label.config(text=f"Current: {self.current_noise_level:.3f}")
                    
                    if noise_detected and noise_cooldown <= 0:
                        self.noise_events += 1
                        self.last_noise_time = time.time()
                        
                        # Update noise status
                        self.noise_status_label.config(
                            text="ACTIVE",
                            foreground=self.alert_color
                        )
                        
                        # Add noise indicator to frame
                        cv2.putText(processed_frame, "NOISE DETECTED", 
                                   (10, 90), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                        
                        # Start recording if enabled
                        if (self.record_on_noise and not self.video_recorder.recording 
                            and not self.auto_record):
                            filename = self.video_recorder.start_recording(processed_frame, reason="noise")
                            self.sound_recorder.start_recording()
                            self.add_event(f"Noise detected - Recording started")
                        
                        noise_cooldown = 5  # Cooldown frames
                    else:
                        if noise_cooldown > 0:
                            noise_cooldown -= 1
                        
                        # Update noise status
                        if time.time() - (self.last_noise_time or 0) < 1:
                            self.noise_status_label.config(
                                text="ACTIVE",
                                foreground=self.alert_color
                            )
                        else:
                            self.noise_status_label.config(
                                text="None",
                                foreground=self.fg_color
                            )
                
                # Handle recording stop after events
                if (not self.auto_record and self.video_recorder.recording and
                    self.last_motion_time and self.last_noise_time):
                    time_since_motion = time.time() - self.last_motion_time
                    time_since_noise = time.time() - self.last_noise_time
                    
                    if (time_since_motion > self.recording_duration and 
                        time_since_noise > self.recording_duration):
                        video_file, duration = self.video_recorder.stop_recording()
                        audio_file = self.sound_recorder.stop_recording()
                        if video_file:
                            reason = self.video_recorder.recording_reason
                            self.add_event(f"Recording stopped - No activity for {self.recording_duration}s")
                
                # Write frame to recording if active
                if self.video_recorder.recording or self.auto_record:
                    self.video_recorder.write_frame(processed_frame)
                    
                    # Add sound wave indicator if noise detected
                    if self.noise_detector and self.current_noise_level > self.noise_threshold:
                        cv2.putText(processed_frame, "🔊", 
                                   (processed_frame.shape[1] - 50, processed_frame.shape[0] - 20), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
                    
                    # Update recording label
                    reason = self.video_recorder.recording_reason if self.video_recorder.recording else "Continuous"
                    self.recording_label.config(
                        text=f"Yes ({reason})",
                        foreground=self.alert_color
                    )
                else:
                    self.recording_label.config(
                        text="No",
                        foreground=self.fg_color
                    )
                
                # Add sound to recording if active
                if self.sound_recorder.recording and self.noise_detector:
                    if not self.noise_detector.audio_queue.empty():
                        audio_data, _ = self.noise_detector.audio_queue.get()
                        self.sound_recorder.add_frame(audio_data)
                
                # Convert frame to RGB for display
                frame_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                
                # Update video display
                self.update_video_display(frame_rgb)
                
                # Update stats
                self.update_stats()
            else:
                logger.warning("Failed to capture frame")
                break
    
    def update_video_display(self, frame):
        """Update the video feed in the GUI"""
        # Resize frame to fit display
        height, width = frame.shape[:2]
        max_height = 500
        max_width = 700
        
        if height > max_height or width > max_width:
            scale = min(max_height/height, max_width/width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        # Convert to PhotoImage
        image = Image.fromarray(frame)
        photo = ImageTk.PhotoImage(image)
        
        # Update label
        self.video_label.config(image=photo)
        self.video_label.image = photo  # Keep a reference
    
    def update_stats(self):
        """Update statistics display"""
        self.motion_label.config(text=str(self.motion_events))
        self.noise_label.config(text=str(self.noise_events))
        self.fps_label.config(text=str(self.fps))
        
        # Update uptime
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

def main():
    """Main entry point"""
    root = tk.Tk()
    app = CypherCam(root)
    
    # Handle window close
    def on_closing():
        if app.is_running:
            app.stop_camera()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()