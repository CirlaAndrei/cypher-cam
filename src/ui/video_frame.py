"""Video display component with improved UI"""
import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk
import time

class VideoFrame(ttk.Frame):
    """Enhanced video display frame with overlays and controls"""
    
    def __init__(self, parent, app, **kwargs):
        super().__init__(parent, **kwargs)
        self.app = app
        self.style = kwargs.get('style')
        
        # Video display
        self.video_label = ttk.Label(self)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # Overlay controls (appears on hover)
        self.create_overlay()
        
        # Status bar below video
        self.create_status_bar()
        
        # Bind hover events
        self.video_label.bind('<Enter>', self.show_overlay)
        self.video_label.bind('<Leave>', self.hide_overlay)
        
        self.overlay_visible = False
    
    def create_overlay(self):
        """Create transparent overlay with quick controls"""
        self.overlay = tk.Frame(self, bg='#000000')
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.lower()  # Start hidden
        
        # Quick control buttons in overlay
        btn_frame = tk.Frame(self.overlay, bg='#000000')
        btn_frame.place(relx=0.5, rely=0.1, anchor='n')
        
        self.record_btn = tk.Button(btn_frame, text='⏺', font=('Arial', 16),
                                    bg='#ff4444', fg='white', bd=0,
                                    command=self.app.toggle_manual_recording)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.snapshot_btn = tk.Button(btn_frame, text='📸', font=('Arial', 16),
                                      bg='#444444', fg='white', bd=0,
                                      command=self.app.take_snapshot)
        self.snapshot_btn.pack(side=tk.LEFT, padx=5)
        
        self.fullscreen_btn = tk.Button(btn_frame, text='⛶', font=('Arial', 16),
                                        bg='#444444', fg='white', bd=0,
                                        command=self.toggle_fullscreen)
        self.fullscreen_btn.pack(side=tk.LEFT, padx=5)
        
        # Status overlay at bottom
        self.status_overlay = tk.Frame(self.overlay, bg='#000000')
        self.status_overlay.place(relx=0, rely=1, relwidth=1, anchor='sw')
        
        self.motion_indicator = tk.Label(self.status_overlay, text='● Motion', 
                                        fg='#888888', bg='#000000', font=('Arial', 9))
        self.motion_indicator.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.noise_indicator = tk.Label(self.status_overlay, text='● Noise',
                                       fg='#888888', bg='#000000', font=('Arial', 9))
        self.noise_indicator.pack(side=tk.LEFT, padx=10, pady=5)
        
        self.rec_indicator = tk.Label(self.status_overlay, text='⏺',
                                      fg='#888888', bg='#000000', font=('Arial', 9))
        self.rec_indicator.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def create_status_bar(self):
        """Create status bar below video"""
        self.status_bar = ttk.Frame(self)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Timestamp
        self.time_label = ttk.Label(self.status_bar, font=('Consolas', 8))
        self.time_label.pack(side=tk.LEFT)
        
        # FPS
        self.fps_label = ttk.Label(self.status_bar, font=('Consolas', 8))
        self.fps_label.pack(side=tk.RIGHT)
        
        # Update time periodically
        self.update_time()
    
    def update_time(self):
        """Update timestamp in status bar"""
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        self.time_label.config(text=current_time)
        self.after(1000, self.update_time)
    
    def show_overlay(self, event=None):
        """Show overlay controls"""
        self.overlay.lift()
        self.overlay_visible = True
    
    def hide_overlay(self, event=None):
        """Hide overlay controls"""
        self.overlay.lower()
        self.overlay_visible = False
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        # Implement fullscreen toggle
        pass
    
    def update_display(self, frame):
        """Update video display with frame"""
        # Resize frame to fit
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
        self.video_label.image = photo
    
    def update_indicators(self, motion=False, noise=False, recording=False):
        """Update status indicators"""
        # Motion indicator
        if motion:
            self.motion_indicator.config(fg='#ff4444', text='● Motion ACTIVE')
        else:
            self.motion_indicator.config(fg='#888888', text='● Motion')
        
        # Noise indicator
        if noise:
            self.noise_indicator.config(fg='#ffaa00', text='● Noise ACTIVE')
        else:
            self.noise_indicator.config(fg='#888888', text='● Noise')
        
        # Recording indicator
        if recording:
            self.rec_indicator.config(fg='#ff4444', text='⏺ REC')
            self.record_btn.config(bg='#ff4444', text='⏸')
        else:
            self.rec_indicator.config(fg='#888888', text='⏺')
            self.record_btn.config(bg='#ff4444', text='⏺')
        
        # Update FPS
        if hasattr(self.app, 'fps'):
            self.fps_label.config(text=f'FPS: {self.app.fps}')