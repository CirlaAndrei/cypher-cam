"""UI styling and themes for the application"""
import tkinter as tk
from tkinter import ttk

class CyberTheme:
    """Cyberpunk-inspired dark theme"""
    
    # Color palette
    BG_DARK = '#0a0e14'
    BG_MEDIUM = '#1a1f2a'
    BG_LIGHT = '#2a3140'
    FG_LIGHT = '#e6e9f0'
    FG_DIM = '#8a9199'
    ACCENT_BLUE = '#2d7cf2'
    ACCENT_CYAN = '#36d6e7'
    ACCENT_PURPLE = '#9f7efe'
    ACCENT_RED = '#f25e5e'
    ACCENT_GREEN = '#41d47d'
    ACCENT_ORANGE = '#fe9f4f'
    
    # Status colors
    SUCCESS = ACCENT_GREEN
    WARNING = ACCENT_ORANGE
    ERROR = ACCENT_RED
    INFO = ACCENT_BLUE
    
    # Fonts
    FONT_FAMILY = 'Segoe UI'
    FONT_SMALL = (FONT_FAMILY, 9)
    FONT_NORMAL = (FONT_FAMILY, 10)
    FONT_MEDIUM = (FONT_FAMILY, 11, 'bold')
    FONT_LARGE = (FONT_FAMILY, 14, 'bold')
    FONT_MONO = ('Consolas', 9)
    
    @classmethod
    def apply_theme(cls, root):
        """Apply the cyber theme to the entire application"""
        root.configure(bg=cls.BG_DARK)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles for different widget types
        style.configure('TFrame', background=cls.BG_DARK)
        style.configure('TLabel', background=cls.BG_DARK, foreground=cls.FG_LIGHT, font=cls.FONT_NORMAL)
        style.configure('TButton', background=cls.BG_MEDIUM, foreground=cls.FG_LIGHT, 
                       font=cls.FONT_NORMAL, borderwidth=1, focusthickness=3)
        style.map('TButton',
                 background=[('active', cls.ACCENT_BLUE), ('pressed', cls.ACCENT_CYAN)],
                 foreground=[('active', cls.FG_LIGHT)])
        
        style.configure('TLabelframe', background=cls.BG_DARK, foreground=cls.FG_LIGHT, 
                       font=cls.FONT_MEDIUM)
        style.configure('TLabelframe.Label', background=cls.BG_DARK, foreground=cls.ACCENT_CYAN, 
                       font=cls.FONT_MEDIUM)
        
        style.configure('TCheckbutton', background=cls.BG_DARK, foreground=cls.FG_LIGHT,
                       font=cls.FONT_NORMAL)
        style.map('TCheckbutton',
                 background=[('active', cls.BG_MEDIUM)],
                 foreground=[('active', cls.FG_LIGHT)])
        
        style.configure('TScale', background=cls.BG_DARK, troughcolor=cls.BG_MEDIUM,
                       sliderlength=20, sliderrelief='flat')
        
        style.configure('TProgressbar', background=cls.ACCENT_CYAN, troughcolor=cls.BG_MEDIUM,
                       borderwidth=0)
        
        style.configure('TScrollbar', background=cls.BG_MEDIUM, troughcolor=cls.BG_DARK,
                       arrowcolor=cls.FG_LIGHT)
        
        # Custom button styles
        style.configure('Success.TButton', background=cls.SUCCESS, foreground=cls.BG_DARK)
        style.map('Success.TButton',
                 background=[('active', cls.ACCENT_GREEN), ('pressed', cls.ACCENT_GREEN)])
        
        style.configure('Danger.TButton', background=cls.ERROR, foreground=cls.BG_DARK)
        style.map('Danger.TButton',
                 background=[('active', cls.ACCENT_RED), ('pressed', cls.ACCENT_RED)])
        
        style.configure('Accent.TButton', background=cls.ACCENT_PURPLE, foreground=cls.BG_DARK)
        style.map('Accent.TButton',
                 background=[('active', cls.ACCENT_PURPLE), ('pressed', cls.ACCENT_PURPLE)])
        
        return style