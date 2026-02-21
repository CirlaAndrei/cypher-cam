"""Control panel for the application"""
import tkinter as tk
from tkinter import ttk
import time

class ControlPanel(ttk.Frame):
    """Control panel with settings and stats"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.style = kwargs.get('style')
        
        # Settings variables
        self.record_on_motion = tk.BooleanVar(value=True)
        self.record_on_noise = tk.BooleanVar(value=True)
        self.auto_record = tk.BooleanVar(value=False)
        self.alert_enabled = tk.BooleanVar(value=True)
        self.recording_duration = tk.IntVar(value=10)
        
        # Create UI
        self.setup_ui()
    
    def setup_ui(self):
        """Create the control panel UI"""
        # Title
        title_label = ttk.Label(
            self, 
            text="CYPHER-CAM",
            font=('Segoe UI', 18, 'bold'),
            foreground='#36d6e7'
        )
        title_label.pack(pady=(0, 20))
        
        # Camera Control Section
        self.create_camera_section()
        
        # Motion Detection Section
        self.create_motion_section()
        
        # Noise Detection Section
        self.create_noise_section()
        
        # Recording Settings Section
        self.create_recording_section()
        
        # Statistics Section
        self.create_stats_section()
        
        # Events Section
        self.create_events_section()
    
    def create_camera_section(self):
        """Create camera control section"""
        camera_frame = ttk.LabelFrame(self, text="Camera Control", padding=10)
        camera_frame.pack(fill=tk.X, pady=5)
        
        self.camera_btn = ttk.Button(
            camera_frame, 
            text="START CAMERA",
            command=self.app.toggle_camera,
            style='Accent.TButton'
        )
        self.camera_btn.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(
            camera_frame,
            text="● Status: Ready",
            font=('Segoe UI', 9)
        )
        self.status_label.pack(pady=5)
    
    def create_motion_section(self):
        """Create motion detection controls"""
        motion_frame = ttk.LabelFrame(self, text="Motion Detection", padding=10)
        motion_frame.pack(fill=tk.X, pady=5)
        
        # Sensitivity slider
        ttk.Label(motion_frame, text="Sensitivity:").pack(anchor=tk.W)
        self.threshold_var = tk.IntVar(value=25)
        threshold_scale = ttk.Scale(
            motion_frame, 
            from_=5, to=50, 
            orient=tk.HORIZONTAL,
            variable=self.threshold_var,
            command=self.update_threshold
        )
        threshold_scale.pack(fill=tk.X, pady=2)
        
        self.threshold_label = ttk.Label(motion_frame, text="Threshold: 25")
        self.threshold_label.pack()
        
        # Min area slider
        ttk.Label(motion_frame, text="Min Area:").pack(anchor=tk.W, pady=(5,0))
        self.area_var = tk.IntVar(value=500)
        area_scale = ttk.Scale(
            motion_frame, 
            from_=100, to=2000, 
            orient=tk.HORIZONTAL,
            variable=self.area_var,
            command=self.update_area
        )
        area_scale.pack(fill=tk.X, pady=2)
        
        self.area_label = ttk.Label(motion_frame, text="Min Area: 500")
        self.area_label.pack()
        
        # Motion status
        self.motion_status = ttk.Label(
            motion_frame, 
            text="● Status: None",
            foreground='#8a9199'
        )
        self.motion_status.pack(pady=5)
    
    def create_noise_section(self):
        """Create noise detection controls"""
        noise_frame = ttk.LabelFrame(self, text="Noise Detection", padding=10)
        noise_frame.pack(fill=tk.X, pady=5)
        
        # Noise threshold slider
        ttk.Label(noise_frame, text="Noise Sensitivity:").pack(anchor=tk.W)
        self.noise_threshold_var = tk.DoubleVar(value=0.1)
        noise_scale = ttk.Scale(
            noise_frame, 
            from_=0.01, to=0.5, 
            orient=tk.HORIZONTAL,
            variable=self.noise_threshold_var,
            command=self.update_noise_threshold
        )
        noise_scale.pack(fill=tk.X, pady=2)
        
        self.noise_threshold_label = ttk.Label(noise_frame, text="Threshold: 0.10")
        self.noise_threshold_label.pack()
        
        # Noise level meter
        level_frame = ttk.Frame(noise_frame)
        level_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(level_frame, text="Level:").pack(side=tk.LEFT)
        self.noise_bar = ttk.Progressbar(
            level_frame, 
            length=150, 
            mode='determinate',
            style='TProgressbar'
        )
        self.noise_bar.pack(side=tk.LEFT, padx=5)
        self.noise_value = ttk.Label(level_frame, text="0.00")
        self.noise_value.pack(side=tk.LEFT)
        
        # Noise status
        self.noise_status = ttk.Label(
            noise_frame, 
            text="● Status: None",
            foreground='#8a9199'
        )
        self.noise_status.pack(pady=5)
    
    def create_recording_section(self):
        """Create recording controls"""
        record_frame = ttk.LabelFrame(self, text="Recording", padding=10)
        record_frame.pack(fill=tk.X, pady=5)
        
        # Checkboxes
        ttk.Checkbutton(
            record_frame, 
            text="Record on Motion",
            variable=self.record_on_motion,
            command=self.toggle_setting
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            record_frame, 
            text="Record on Noise",
            variable=self.record_on_noise,
            command=self.toggle_setting
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            record_frame, 
            text="Continuous Recording",
            variable=self.auto_record,
            command=self.toggle_setting
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            record_frame, 
            text="Sound Alerts",
            variable=self.alert_enabled,
            command=self.toggle_setting
        ).pack(anchor=tk.W, pady=2)
        
        # Duration selector
        duration_frame = ttk.Frame(record_frame)
        duration_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duration_frame, text="Stop after:").pack(side=tk.LEFT)
        duration_spin = ttk.Spinbox(
            duration_frame,
            from_=5, to=60,
            textvariable=self.recording_duration,
            width=5,
            command=self.update_duration
        )
        duration_spin.pack(side=tk.LEFT, padx=5)
        ttk.Label(duration_frame, text="sec").pack(side=tk.LEFT)
        
        # Manual recording button
        self.manual_btn = ttk.Button(
            record_frame,
            text="⏺ MANUAL RECORD",
            command=self.app.toggle_manual_recording,
            style='Danger.TButton'
        )
        self.manual_btn.pack(fill=tk.X, pady=5)
        
        # Recording indicator
        self.recording_indicator = ttk.Label(
            record_frame,
            text="● Not Recording",
            foreground='#8a9199'
        )
        self.recording_indicator.pack()
    
    def create_stats_section(self):
        """Create statistics display"""
        stats_frame = ttk.LabelFrame(self, text="Statistics", padding=10)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # Create grid for stats
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        # Row 1
        ttk.Label(stats_grid, text="Motion Events:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.motion_events_label = ttk.Label(stats_grid, text="0")
        self.motion_events_label.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(10,0))
        
        ttk.Label(stats_grid, text="Noise Events:", font=('Segoe UI', 9, 'bold')).grid(row=0, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.noise_events_label = ttk.Label(stats_grid, text="0")
        self.noise_events_label.grid(row=0, column=3, sticky=tk.W, pady=2, padx=(10,0))
        
        # Row 2
        ttk.Label(stats_grid, text="FPS:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.fps_label = ttk.Label(stats_grid, text="0")
        self.fps_label.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(10,0))
        
        ttk.Label(stats_grid, text="Uptime:", font=('Segoe UI', 9, 'bold')).grid(row=1, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.uptime_label = ttk.Label(stats_grid, text="00:00:00")
        self.uptime_label.grid(row=1, column=3, sticky=tk.W, pady=2, padx=(10,0))
    
    def create_events_section(self):
        """Create events log"""
        events_frame = ttk.LabelFrame(self, text="Recent Events", padding=10)
        events_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(events_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.events_listbox = tk.Listbox(
            listbox_frame, 
            height=6,
            bg='#1a1f2a',
            fg='#e6e9f0',
            selectbackground='#2d7cf2',
            font=('Consolas', 8)
        )
        self.events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.events_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Clear button
        ttk.Button(
            events_frame,
            text="Clear Events",
            command=self.clear_events
        ).pack(pady=5)
    
    def update_threshold(self, value):
        """Update motion threshold"""
        val = int(float(value))
        self.threshold_label.config(text=f"Threshold: {val}")
        if hasattr(self.app, 'motion_detector'):
            self.app.motion_detector.threshold = val
    
    def update_area(self, value):
        """Update min area"""
        val = int(float(value))
        self.area_label.config(text=f"Min Area: {val}")
        if hasattr(self.app, 'motion_detector'):
            self.app.motion_detector.min_area = val
    
    def update_noise_threshold(self, value):
        """Update noise threshold"""
        val = float(value)
        self.noise_threshold_label.config(text=f"Threshold: {val:.2f}")
        if hasattr(self.app, 'noise_detector'):
            self.app.noise_detector.threshold = val
    
    def toggle_setting(self):
        """Handle setting toggles"""
        # Update app settings
        self.app.record_on_motion = self.record_on_motion.get()
        self.app.record_on_noise = self.record_on_noise.get()
        self.app.auto_record = self.auto_record.get()
        self.app.alert_enabled = self.alert_enabled.get()
    
    def update_duration(self):
        """Update recording duration"""
        self.app.recording_duration = self.recording_duration.get()
    
    def update_status(self, status):
        """Update camera status"""
        self.status_label.config(text=f"● Status: {status}")
    
    def update_motion_status(self, active):
        """Update motion status indicator"""
        if active:
            self.motion_status.config(text="● Status: ACTIVE", foreground='#f25e5e')
        else:
            self.motion_status.config(text="● Status: None", foreground='#8a9199')
    
    def update_noise_status(self, active):
        """Update noise status indicator"""
        if active:
            self.noise_status.config(text="● Status: ACTIVE", foreground='#fe9f4f')
        else:
            self.noise_status.config(text="● Status: None", foreground='#8a9199')
    
    def update_noise_level(self, level):
        """Update noise level meter"""
        # Scale to percentage (max 0.5)
        percent = min(100, (level / 0.5) * 100)
        self.noise_bar['value'] = percent
        self.noise_value.config(text=f"{level:.3f}")
    
    def update_fps(self, fps):
        """Update FPS display"""
        self.fps_label.config(text=str(fps))
    
    def update_stats(self, motion_events, noise_events, uptime):
        """Update statistics"""
        self.motion_events_label.config(text=str(motion_events))
        self.noise_events_label.config(text=str(noise_events))
        
        # Format uptime
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_recording_button(self, recording=False, reset=False):
        """Update recording button state"""
        if recording:
            self.camera_btn.config(text="STOP CAMERA")
            self.manual_btn.config(text="⏸ STOP RECORDING")
            self.recording_indicator.config(text="● Recording", foreground='#f25e5e')
        elif reset:
            self.camera_btn.config(text="START CAMERA")
            self.manual_btn.config(text="⏺ MANUAL RECORD")
            self.recording_indicator.config(text="● Not Recording", foreground='#8a9199')
    
    def get_setting(self, key):
        """Get setting value"""
        if key == 'record_on_motion':
            return self.record_on_motion.get()
        elif key == 'record_on_noise':
            return self.record_on_noise.get()
        elif key == 'auto_record':
            return self.auto_record.get()
        elif key == 'alert_enabled':
            return self.alert_enabled.get()
        elif key == 'recording_duration':
            return self.recording_duration.get()
        return None
    
    def add_event(self, event_text):
        """Add event to log"""
        timestamp = time.strftime('%H:%M:%S')
        self.events_listbox.insert(0, f"[{timestamp}] {event_text}")
        # Keep only last 20 events
        while self.events_listbox.size() > 20:
            self.events_listbox.delete(20)
    
    def clear_events(self):
        """Clear all events"""
        self.events_listbox.delete(0, tk.END)