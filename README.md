# Cypher-Cam Surveillance System

A feature-rich surveillance system built with Python that turns your webcam into an intelligent security camera.

## Features

### Core Features
- Real-time motion detection with heatmap visualization
- Noise/sound detection with visual level meter
- People and object detection using AI
- Automatic video recording with audio
- Manual recording and snapshot capture
- Dark mode cyberpunk-themed GUI

### Advanced Features
- Web interface for remote viewing (http://localhost:5000)
- Email alerts with snapshot attachments (Gmail compatible)
- Configurable motion sensitivity and detection zones
- Performance optimizations with frame skipping
- Event logging with timestamp history
- FPS counter and system uptime display

### Detection Capabilities
- Motion detection with adjustable threshold and minimum area
- Noise detection with sensitivity control
- Object detection (people, cars, animals, etc.)
- People counting in frame
- Heatmap overlay of motion patterns

## Installation

1. Clone the repository:
git clone https://github.com/CirlaAndrei/cypher-cam.git
cd cypher-cam

2. Create virtual environment:

python -m venv venv

3. Activate virtual environment:
- Windows:
  ```
  venv\Scripts\activate
  ```
- Mac/Linux:
  ```
  source venv/bin/activate
  ```

4. Install dependencies:

5. Run the application:


## Usage Guide

### Getting Started
1. Launch the application with `python src/main.py`
2. Click "START CAMERA" to begin surveillance
3. Adjust detection settings in the control panel
4. Monitor events in real-time through the GUI or web interface

### Web Interface
- Access at: `http://localhost:5000`
- View live feed from any device on your network
- Take snapshots and control recording remotely
- Monitor statistics in real-time

### Email Alerts Configuration
1. Go to Email Alerts section in control panel
2. Click "Configure Email"
3. Enter your email settings (Gmail recommended)
4. Generate an App Password at: https://myaccount.google.com/apppasswords
5. Test connection and enable alerts
6. Choose which events trigger emails (motion, noise, people)

### Controls
- **Camera Control**: Start/stop camera feed
- **Motion Detection**: Adjust sensitivity and minimum area
- **Noise Detection**: Set threshold and monitor levels
- **Object Detection**: Configure confidence threshold
- **Recording**: Toggle automatic or manual recording
- **Email Alerts**: Enable and configure email notifications

### Keyboard Shortcuts
- Click camera feed to show overlay controls
- Use snapshot button (📸) to capture images
- Manual recording button (⏺) for video capture

## Configuration

Settings are saved automatically in the `config` directory:
- `email_config.json` - Email server settings
- Recordings are stored in the `recordings` folder
- Logs are saved in the `logs` directory

## Requirements

- Python 3.8 or higher
- Webcam
- Microphone (optional, for noise detection)
- Internet connection (for email alerts)

## Dependencies

- opencv-python - Computer vision and camera handling
- numpy - Numerical operations
- Pillow - Image processing
- sounddevice - Audio capture
- pygame - Sound alerts
- schedule - Scheduled tasks
- flask - Web interface
- flask-cors - Web security
- secure-smtplib - Email alerts

## Project Structure
cypher-cam/
├── src/
│ ├── main.py # Entry point
│ ├── app.py # Main application class
│ ├── detectors/ # Detection modules
│ │ ├── motion_detector.py
│ │ ├── noise_detector.py
│ │ └── object_detector.py
│ ├── recording/ # Recording modules
│ │ ├── video_recorder.py
│ │ └── audio_recorder.py
│ ├── ui/ # User interface
│ │ ├── styles.py
│ │ ├── video_frame.py
│ │ └── control_panel.py
│ ├── utils/ # Utilities
│ │ ├── logger.py
│ │ ├── camera_utils.py
│ │ └── email_alerts.py
│ └── web_server.py # Flask web interface
├── recordings/ # Saved videos and snapshots
├── config/ # Configuration files
├── logs/ # Application logs
├── requirements.txt # Python dependencies
└── README.md # This file


## Troubleshooting

### Camera Issues
- If camera doesn't start, check if another app is using it
- Try restarting the application
- Update camera drivers

### Email Problems
- Use Gmail App Password, not regular password
- Check spam folder for alerts
- Verify SMTP settings are correct

### Performance
- Adjust frame skip settings in app.py if needed
- Lower resolution in camera settings for better performance
- Disable heatmap effect for faster processing

## Future Enhancements

- Motion heatmap over time visualization
- Cloud backup integration (Google Drive, Dropbox)
- Face recognition for known individuals
- Scheduled recording modes
- Multi-camera support
- Mobile app for notifications

## License

MIT License - feel free to use and modify for your own projects

## Author

Created by CirlaAndrei

## Acknowledgments

- OpenCV for computer vision capabilities
- Flask for web interface framework
- The Python community for excellent libraries

---

**Note**: This is a surveillance system for legitimate security purposes. Please respect privacy laws and use responsibly.
