\"\"\"
Cypher-Cam Surveillance System
Main entry point for the application
\"\"\"

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
import threading
import time
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CypherCam:
    \"\"\"Main application class for Cypher-Cam Surveillance System\"\"\"
    
    def __init__(self, root):
        self.root = root
        self.root.title("Cypher-Cam Surveillance System")
        self.root.geometry("1200x700")
        
        # Set dark mode colors
        self.bg_color = '#1e1e1e'
        self.fg_color = '#ffffff'
        self.accent_color = '#007acc'
        
        self.root.configure(bg=self.bg_color)
        
        # Video capture
        self.cap = None
        self.is_running = False
        self.current_frame = None
        
        # Initialize UI
        self.setup_ui()
        
        logger.info("Cypher-Cam initialized")
    
    def setup_ui(self):
        \"\"\"Setup the user interface\"\"\"
        # Create main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style configuration for dark mode
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', background=self.accent_color, foreground=self.fg_color)
        
        # Video feed frame (left side)
        video_frame = ttk.Frame(main_frame)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.video_label = ttk.Label(video_frame)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Control panel (right side)
        control_frame = ttk.Frame(main_frame, width=250)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        control_frame.pack_propagate(False)
        
        # Title
        title_label = ttk.Label(
            control_frame, 
            text="Cypher-Cam Controls",
            font=('Arial', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Camera controls
        self.start_button = ttk.Button(
            control_frame,
            text="Start Camera",
            command=self.toggle_camera
        )
        self.start_button.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_label = ttk.Label(
            control_frame,
            text="Status: Ready",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=10)
        
        # Stats section
        stats_frame = ttk.LabelFrame(control_frame, text="Statistics")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.motion_label = ttk.Label(stats_frame, text="Motion: 0")
        self.motion_label.pack(pady=2)
        
        self.noise_label = ttk.Label(stats_frame, text="Noise: 0")
        self.noise_label.pack(pady=2)
        
        self.people_label = ttk.Label(stats_frame, text="People count: 0")
        self.people_label.pack(pady=2)
        
        self.recording_label = ttk.Label(stats_frame, text="Recording: No")
        self.recording_label.pack(pady=2)
        
        logger.info("UI setup complete")
    
    def toggle_camera(self):
        \"\"\"Start or stop the camera\"\"\"
        if not self.is_running:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        \"\"\"Initialize and start the camera\"\"\"
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                logger.error("Could not open camera")
                return
            
            self.is_running = True
            self.start_button.config(text="Stop Camera")
            self.status_label.config(text="Status: Camera Running")
            
            # Start video processing thread
            self.video_thread = threading.Thread(target=self.process_video)
            self.video_thread.daemon = True
            self.video_thread.start()
            
            logger.info("Camera started")
        except Exception as e:
            logger.error(f"Error starting camera: {e}")
    
    def stop_camera(self):
        \"\"\"Stop the camera\"\"\"
        self.is_running = False
        if self.cap:
            self.cap.release()
        
        self.start_button.config(text="Start Camera")
        self.status_label.config(text="Status: Ready")
        logger.info("Camera stopped")
    
    def process_video(self):
        \"\"\"Main video processing loop\"\"\"
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                # Convert frame to RGB for display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.current_frame = frame_rgb
                
                # Update video display
                self.update_video_display(frame_rgb)
                
                # Placeholder for detection logic
                self.update_stats()
            else:
                logger.warning("Failed to capture frame")
                break
            
            time.sleep(0.03)  # ~30 FPS
    
    def update_video_display(self, frame):
        \"\"\"Update the video feed in the GUI\"\"\"
        # Resize frame to fit display
        height, width = frame.shape[:2]
        max_height = 600
        max_width = 800
        
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
        \"\"\"Update statistics display\"\"\"
        # Placeholder - will be replaced with actual detection
        self.motion_label.config(text="Motion: 0 (Placeholder)")
        self.noise_label.config(text="Noise: 0 (Placeholder)")
        self.people_label.config(text="People count: 0 (Placeholder)")
        self.recording_label.config(text="Recording: No (Placeholder)")

def main():
    \"\"\"Main entry point\"\"\"
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
