"""Control panel for the application"""
import tkinter as tk
from tkinter import ttk
import time
from tkinter import simpledialog, messagebox

class ControlPanel(ttk.Frame):
    """Control panel with settings and stats"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Configure the frame
        self.configure(relief='flat', padding=10)
        
        # Settings variables
        self.record_on_motion = tk.BooleanVar(value=True)
        self.record_on_noise = tk.BooleanVar(value=True)
        self.auto_record = tk.BooleanVar(value=False)
        self.alert_enabled = tk.BooleanVar(value=True)
        self.recording_duration = tk.IntVar(value=10)
        self.show_heatmap = tk.BooleanVar(value=True)
        
        # Email settings variables
        self.email_enabled = tk.BooleanVar(value=False)
        self.email_on_motion = tk.BooleanVar(value=True)
        self.email_on_noise = tk.BooleanVar(value=False)
        self.email_on_people = tk.BooleanVar(value=True)
        
        # Create UI
        self.setup_ui()
    
    def setup_ui(self):
        """Create the control panel UI"""
        # Title
        title_label = ttk.Label(
            self, 
            text="CYPHER-CAM",
            font=('Segoe UI', 18, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # Camera Control Section
        self.create_camera_section()
        
        # Motion Detection Section
        self.create_motion_section()
        
        # Noise Detection Section
        self.create_noise_section()
        
        # Object Detection Section
        self.create_object_section()
        
        # Recording Settings Section
        self.create_recording_section()

        # Email Section
        self.create_email_section()
        
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
            command=self.app.toggle_camera
        )
        self.camera_btn.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(
            camera_frame,
            text="● Status: Ready"
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
        
        # Heatmap toggle
        ttk.Checkbutton(
            motion_frame, 
            text="Show Heatmap Effect",
            variable=self.show_heatmap,
            command=self.toggle_heatmap
        ).pack(anchor=tk.W, pady=5)
        
        # Motion status
        self.motion_status = ttk.Label(
            motion_frame, 
            text="● Status: None"
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
            mode='determinate'
        )
        self.noise_bar.pack(side=tk.LEFT, padx=5)
        self.noise_value = ttk.Label(level_frame, text="0.00")
        self.noise_value.pack(side=tk.LEFT)
        
        # Noise status
        self.noise_status = ttk.Label(
            noise_frame, 
            text="● Status: None"
        )
        self.noise_status.pack(pady=5)
    
    def create_object_section(self):
        """Create object detection controls"""
        object_frame = ttk.LabelFrame(self, text="Object Detection", padding=10)
        object_frame.pack(fill=tk.X, pady=5)
        
        # Confidence threshold slider
        ttk.Label(object_frame, text="Confidence:").pack(anchor=tk.W)
        self.confidence_var = tk.DoubleVar(value=0.5)
        confidence_scale = ttk.Scale(
            object_frame, 
            from_=0.1, to=0.9, 
            orient=tk.HORIZONTAL,
            variable=self.confidence_var,
            command=self.update_confidence
        )
        confidence_scale.pack(fill=tk.X, pady=2)
        
        self.confidence_label = ttk.Label(object_frame, text="Confidence: 0.50")
        self.confidence_label.pack()
        
        # Detected objects list
        objects_frame = ttk.Frame(object_frame)
        objects_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(objects_frame, text="Detected:").pack(side=tk.LEFT)
        self.objects_list = ttk.Label(objects_frame, text="None")
        self.objects_list.pack(side=tk.LEFT, padx=5)
    
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
            text="Record on Objects",
            variable=tk.BooleanVar(value=False),
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
            command=self.app.toggle_manual_recording
        )
        self.manual_btn.pack(fill=tk.X, pady=5)
        
        # Recording indicator
        self.recording_indicator = ttk.Label(
            record_frame,
            text="● Not Recording"
        )
        self.recording_indicator.pack()
    
    def create_email_section(self):
        """Create email alert settings section"""
        email_frame = ttk.LabelFrame(self, text="Email Alerts", padding=10)
        email_frame.pack(fill=tk.X, pady=5)
        
        # Email toggle
        ttk.Checkbutton(
            email_frame, 
            text="Enable Email Alerts",
            variable=self.email_enabled,
            command=self.toggle_email
        ).pack(anchor=tk.W, pady=2)
        
        # Status indicator
        self.email_status = ttk.Label(email_frame, text="● Not Configured", foreground='#8a9199')
        self.email_status.pack(anchor=tk.W, pady=2)
        
        # Configure button
        self.email_config_btn = ttk.Button(
            email_frame,
            text="⚙️ Configure Email",
            command=self.configure_email
        )
        self.email_config_btn.pack(fill=tk.X, pady=2)
        
        # Test button
        self.email_test_btn = ttk.Button(
            email_frame,
            text="📧 Test Connection",
            command=self.test_email,
            state='disabled'
        )
        self.email_test_btn.pack(fill=tk.X, pady=2)
        
        # Alert options
        ttk.Checkbutton(
            email_frame, 
            text="Alert on Motion",
            variable=self.email_on_motion,
            command=self.toggle_email_setting
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            email_frame, 
            text="Alert on Noise",
            variable=self.email_on_noise,
            command=self.toggle_email_setting
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Checkbutton(
            email_frame, 
            text="Alert on People Detected",
            variable=self.email_on_people,
            command=self.toggle_email_setting
        ).pack(anchor=tk.W, pady=2)
        
        # Cooldown selector
        cooldown_frame = ttk.Frame(email_frame)
        cooldown_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cooldown_frame, text="Cooldown:").pack(side=tk.LEFT)
        self.email_cooldown = ttk.Spinbox(
            cooldown_frame,
            from_=10, to=300,
            width=5,
            command=self.update_email_cooldown
        )
        self.email_cooldown.pack(side=tk.LEFT, padx=5)
        ttk.Label(cooldown_frame, text="seconds").pack(side=tk.LEFT)
    
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

        # Row 3
        ttk.Label(stats_grid, text="People:", font=('Segoe UI', 9, 'bold')).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.people_label = ttk.Label(stats_grid, text="0")
        self.people_label.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(10,0))
        
        ttk.Label(stats_grid, text="Objects:", font=('Segoe UI', 9, 'bold')).grid(row=2, column=2, sticky=tk.W, pady=2, padx=(20,0))
        self.objects_count_label = ttk.Label(stats_grid, text="0")
        self.objects_count_label.grid(row=2, column=3, sticky=tk.W, pady=2, padx=(10,0))
    
    def create_events_section(self):
        """Create events log"""
        events_frame = ttk.LabelFrame(self, text="Recent Events", padding=10)
        events_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(events_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.events_listbox = tk.Listbox(
            listbox_frame, 
            height=8,
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
    
    # Update methods
    def update_threshold(self, value):
        val = int(float(value))
        self.threshold_label.config(text=f"Threshold: {val}")
        if hasattr(self.app, 'motion_detector'):
            self.app.motion_detector.threshold = val
    
    def update_area(self, value):
        val = int(float(value))
        self.area_label.config(text=f"Min Area: {val}")
        if hasattr(self.app, 'motion_detector'):
            self.app.motion_detector.min_area = val
    
    def update_noise_threshold(self, value):
        val = float(value)
        self.noise_threshold_label.config(text=f"Threshold: {val:.2f}")
        if hasattr(self.app, 'noise_detector'):
            self.app.noise_detector.threshold = val
    
    def update_confidence(self, value):
        val = float(value)
        self.confidence_label.config(text=f"Confidence: {val:.2f}")
        if hasattr(self.app, 'object_detector'):
            self.app.object_detector.confidence_threshold = val
    
    def toggle_heatmap(self):
        if hasattr(self.app, 'toggle_heatmap'):
            self.app.toggle_heatmap(self.show_heatmap.get())
    
    def toggle_setting(self):
        self.app.record_on_motion = self.record_on_motion.get()
        self.app.record_on_noise = self.record_on_noise.get()
        self.app.auto_record = self.auto_record.get()
        self.app.alert_enabled = self.alert_enabled.get()
    
    def update_duration(self):
        self.app.recording_duration = self.recording_duration.get()
    
    def update_status(self, status):
        self.status_label.config(text=f"● Status: {status}")
    
    def update_motion_status(self, active):
        if active:
            self.motion_status.config(text="● Status: ACTIVE")
        else:
            self.motion_status.config(text="● Status: None")
    
    def update_noise_status(self, active):
        if active:
            self.noise_status.config(text="● Status: ACTIVE")
        else:
            self.noise_status.config(text="● Status: None")
    
    def update_noise_level(self, level):
        percent = min(100, (level / 0.5) * 100)
        self.noise_bar['value'] = percent
        self.noise_value.config(text=f"{level:.3f}")
    
    def update_fps(self, fps):
        self.fps_label.config(text=str(fps))
    
    def update_stats(self, motion_events, noise_events, uptime, people_count=0, objects_count=0):
        self.motion_events_label.config(text=str(motion_events))
        self.noise_events_label.config(text=str(noise_events))
        
        if hasattr(self, 'people_label'):
            self.people_label.config(text=str(people_count))
        
        if hasattr(self, 'objects_count_label'):
            self.objects_count_label.config(text=str(objects_count))
        
        if hasattr(self.app, 'detected_objects'):
            object_types = {}
            for obj in self.app.detected_objects:
                class_name = obj['class']
                object_types[class_name] = object_types.get(class_name, 0) + 1
            
            if object_types:
                objects_text = ", ".join([f"{k}:{v}" for k, v in object_types.items()])
                self.objects_list.config(text=objects_text)
            else:
                self.objects_list.config(text="None")
        
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
    
    def update_recording_button(self, recording=False, reset=False):
        if recording:
            self.camera_btn.config(text="STOP CAMERA")
            self.manual_btn.config(text="⏸ STOP RECORDING")
            self.recording_indicator.config(text="● Recording")
        elif reset:
            self.camera_btn.config(text="START CAMERA")
            self.manual_btn.config(text="⏺ MANUAL RECORD")
            self.recording_indicator.config(text="● Not Recording")
    
    def get_setting(self, key):
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
        elif key == 'show_heatmap':
            return self.show_heatmap.get()
        return None
    
    def add_event(self, event_text):
        timestamp = time.strftime('%H:%M:%S')
        self.events_listbox.insert(0, f"[{timestamp}] {event_text}")
        while self.events_listbox.size() > 20:
            self.events_listbox.delete(20)
    
    def clear_events(self):
        self.events_listbox.delete(0, tk.END)
    
    # Email methods
    def toggle_email(self):
        """Toggle email alerts"""
        if hasattr(self.app, 'email_alerts'):
            self.app.email_alerts.enabled = self.email_enabled.get()
            self.update_email_status()
    
    def toggle_email_setting(self):
        """Toggle individual email alert settings"""
        if hasattr(self.app, 'email_settings'):
            self.app.email_settings = {
                'motion': self.email_on_motion.get(),
                'noise': self.email_on_noise.get(),
                'people': self.email_on_people.get()
            }
    
    def update_email_cooldown(self):
        """Update email cooldown"""
        if hasattr(self.app, 'email_alerts'):
            self.app.email_alerts.alert_cooldown = int(self.email_cooldown.get())
    
    def configure_email(self):
        """Open email configuration dialog"""
        if not hasattr(self.app, 'email_alerts'):
            messagebox.showerror("Error", "Email system not initialized")
            return
        
        dialog = tk.Toplevel(self)
        dialog.title("Email Configuration")
        dialog.geometry("500x450")
        dialog.configure(bg='#0a0e14')
        dialog.transient(self)
        dialog.grab_set()
        dialog.focus_set()
        
        # Title
        ttk.Label(dialog, text="Email Alert Settings", 
                  font=('Segoe UI', 14, 'bold')).pack(pady=10)
        
        # Create form
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # SMTP Server
        ttk.Label(frame, text="SMTP Server:").pack(anchor=tk.W, pady=(5,0))
        smtp_entry = ttk.Entry(frame, width=40)
        smtp_entry.insert(0, getattr(self.app.email_alerts, 'smtp_server', 'smtp.gmail.com'))
        smtp_entry.pack(fill=tk.X, pady=2)
        
        # SMTP Port
        ttk.Label(frame, text="Port:").pack(anchor=tk.W, pady=(5,0))
        port_entry = ttk.Entry(frame, width=10)
        port_entry.insert(0, str(getattr(self.app.email_alerts, 'smtp_port', 587)))
        port_entry.pack(anchor=tk.W, pady=2)
        
        # Sender Email
        ttk.Label(frame, text="Sender Email:").pack(anchor=tk.W, pady=(5,0))
        sender_entry = ttk.Entry(frame, width=40)
        sender_entry.insert(0, getattr(self.app.email_alerts, 'sender_email', ''))
        sender_entry.pack(fill=tk.X, pady=2)
        
        # Sender Password
        ttk.Label(frame, text="Password (App Password for Gmail):").pack(anchor=tk.W, pady=(5,0))
        password_entry = ttk.Entry(frame, width=40, show='*')
        password_entry.insert(0, getattr(self.app.email_alerts, 'sender_password', ''))
        password_entry.pack(fill=tk.X, pady=2)
        
        # Recipient Email
        ttk.Label(frame, text="Recipient Email:").pack(anchor=tk.W, pady=(5,0))
        recipient_entry = ttk.Entry(frame, width=40)
        recipient_entry.insert(0, getattr(self.app.email_alerts, 'recipient_email', ''))
        recipient_entry.pack(fill=tk.X, pady=2)
        
        # Note
        note = tk.Message(frame, 
                         text="For Gmail, use an App Password (not regular password)\nGet one: https://myaccount.google.com/apppasswords",
                         width=400, bg='#1a1f2a', fg='#fe9f4f')
        note.pack(pady=10)
        
        # Buttons
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def save_settings():
            self.app.email_alerts.update_settings(
                enabled=self.email_enabled.get(),
                sender_email=sender_entry.get(),
                sender_password=password_entry.get(),
                recipient_email=recipient_entry.get(),
                smtp_server=smtp_entry.get(),
                smtp_port=int(port_entry.get()),
                cooldown=int(self.email_cooldown.get())
            )
            self.update_email_status()
            dialog.destroy()
            messagebox.showinfo("Success", "Email settings saved!")
        
        ttk.Button(button_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        def test_connection():
            success, msg = self.app.email_alerts.test_connection()
            if success:
                messagebox.showinfo("Success", "Email connection successful!")
            else:
                messagebox.showerror("Error", f"Connection failed:\n{msg}")
        
        ttk.Button(button_frame, text="Test Connection", command=test_connection).pack(side=tk.RIGHT, padx=5)
    
    def test_email(self):
        """Test email configuration"""
        if hasattr(self.app, 'email_alerts'):
            success, msg = self.app.email_alerts.test_connection()
            if success:
                messagebox.showinfo("Success", "Email connection successful!")
            else:
                messagebox.showerror("Error", f"Connection failed:\n{msg}")
    
    def update_email_status(self):
        """Update email status indicator"""
        if hasattr(self.app, 'email_alerts') and self.app.email_alerts.enabled:
            if self.app.email_alerts.sender_email:
                self.email_status.config(text="● Enabled", foreground='#41d47d')
                self.email_test_btn.config(state='normal')
            else:
                self.email_status.config(text="● Not Configured", foreground='#fe9f4f')
                self.email_test_btn.config(state='disabled')
        else:
            self.email_status.config(text="● Disabled", foreground='#8a9199')
            self.email_test_btn.config(state='disabled')