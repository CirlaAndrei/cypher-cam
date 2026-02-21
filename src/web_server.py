"""Web interface for Cypher-Cam using Flask"""
from flask import Flask, Response, render_template_string, jsonify
import cv2
import threading
import time
import json
from datetime import datetime

class WebServer:
    """Simple web server to stream video and stats"""
    
    def __init__(self, app, port=5000):
        self.app = app
        self.port = port
        self.flask_app = Flask(__name__)
        self.setup_routes()
        self.server_thread = None
        self.running = False
        
    def setup_routes(self):
        @self.flask_app.route('/')
        def index():
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Cypher-Cam Web Interface</title>
                <style>
                    body {
                        background: #0a0e14;
                        color: #e6e9f0;
                        font-family: 'Segoe UI', sans-serif;
                        margin: 0;
                        padding: 20px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    h1 {
                        color: #36d6e7;
                        border-bottom: 2px solid #2d7cf2;
                        padding-bottom: 10px;
                    }
                    .video-container {
                        background: #1a1f2a;
                        border-radius: 10px;
                        padding: 20px;
                        margin: 20px 0;
                        box-shadow: 0 0 20px rgba(45, 124, 242, 0.3);
                    }
                    .video-feed {
                        width: 100%;
                        border-radius: 5px;
                        border: 2px solid #2d7cf2;
                    }
                    .stats {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }
                    .stat-card {
                        background: #1a1f2a;
                        border-radius: 8px;
                        padding: 15px;
                        border-left: 4px solid #36d6e7;
                    }
                    .stat-label {
                        color: #8a9199;
                        font-size: 0.9em;
                    }
                    .stat-value {
                        color: #36d6e7;
                        font-size: 2em;
                        font-weight: bold;
                    }
                    .events {
                        background: #1a1f2a;
                        border-radius: 8px;
                        padding: 15px;
                        max-height: 300px;
                        overflow-y: auto;
                    }
                    .event {
                        padding: 8px;
                        border-bottom: 1px solid #2a3140;
                        font-family: monospace;
                    }
                    .event-time {
                        color: #fe9f4f;
                    }
                    .controls {
                        display: flex;
                        gap: 10px;
                        margin: 20px 0;
                    }
                    .btn {
                        background: #2d7cf2;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 1em;
                    }
                    .btn:hover {
                        background: #36d6e7;
                    }
                    .btn-danger {
                        background: #f25e5e;
                    }
                    .btn-success {
                        background: #41d47d;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🔒 Cypher-Cam Surveillance</h1>
                    
                    <div class="video-container">
                        <img src="/video_feed" class="video-feed" alt="Live Feed">
                    </div>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-label">Motion Events</div>
                            <div class="stat-value" id="motion">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Noise Events</div>
                            <div class="stat-value" id="noise">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">People Count</div>
                            <div class="stat-value" id="people">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">FPS</div>
                            <div class="stat-value" id="fps">0</div>
                        </div>
                    </div>
                    
                    <div class="controls">
                        <button class="btn btn-success" onclick="takeSnapshot()">📸 Take Snapshot</button>
                        <button class="btn" onclick="toggleRecording()">⏺ Toggle Recording</button>
                        <button class="btn btn-danger" onclick="clearEvents()">🗑️ Clear Events</button>
                    </div>
                    
                    <div class="events" id="events">
                        <div class="event">System connected</div>
                    </div>
                </div>
                
                <script>
                    function updateStats() {
                        fetch('/api/stats')
                            .then(res => res.json())
                            .then(data => {
                                document.getElementById('motion').textContent = data.motion_events;
                                document.getElementById('noise').textContent = data.noise_events;
                                document.getElementById('people').textContent = data.people_count;
                                document.getElementById('fps').textContent = data.fps;
                            });
                    }
                    
                    function updateEvents() {
                        fetch('/api/events')
                            .then(res => res.json())
                            .then(data => {
                                let eventsHtml = '';
                                data.events.forEach(event => {
                                    eventsHtml += `<div class="event"><span class="event-time">[${event.time}]</span> ${event.text}</div>`;
                                });
                                document.getElementById('events').innerHTML = eventsHtml;
                            });
                    }
                    
                    function takeSnapshot() {
                        fetch('/api/snapshot', {method: 'POST'})
                            .then(() => alert('Snapshot taken!'));
                    }
                    
                    function toggleRecording() {
                        fetch('/api/toggle_recording', {method: 'POST'})
                            .then(res => res.json())
                            .then(data => alert(data.message));
                    }
                    
                    function clearEvents() {
                        fetch('/api/clear_events', {method: 'POST'})
                            .then(() => updateEvents());
                    }
                    
                    setInterval(updateStats, 1000);
                    setInterval(updateEvents, 2000);
                </script>
            </body>
            </html>
            ''')
        
        @self.flask_app.route('/video_feed')
        def video_feed():
            return Response(self.generate_frames(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.flask_app.route('/api/stats')
        def get_stats():
            return jsonify({
                'motion_events': self.app.motion_events,
                'noise_events': self.app.noise_events,
                'people_count': getattr(self.app, 'people_count', 0),
                'fps': self.app.fps,
                'recording': self.app.video_recorder.recording
            })
        
        @self.flask_app.route('/api/events')
        def get_events():
            events = []
            if hasattr(self.app.control_panel, 'events_listbox'):
                # Get last 10 events from listbox
                items = self.app.control_panel.events_listbox.get(0, 9)
                for item in items:
                    if item:
                        # Parse timestamp and text
                        if ']' in item:
                            time_part, text = item.split(']', 1)
                            time = time_part.strip('[')
                            events.append({'time': time, 'text': text.strip()})
            return jsonify({'events': events})
        
        @self.flask_app.route('/api/snapshot', methods=['POST'])
        def take_snapshot():
            self.app.take_snapshot()
            return jsonify({'status': 'success'})
        
        @self.flask_app.route('/api/toggle_recording', methods=['POST'])
        def toggle_recording():
            self.app.toggle_manual_recording()
            status = 'Recording started' if self.app.video_recorder.recording else 'Recording stopped'
            return jsonify({'message': status})
        
        @self.flask_app.route('/api/clear_events', methods=['POST'])
        def clear_events():
            self.app.control_panel.clear_events()
            return jsonify({'status': 'success'})
    
    def generate_frames(self):
        """Generate video frames for streaming"""
        while True:
            if hasattr(self.app, 'current_frame') and self.app.current_frame is not None:
                # Get the latest frame
                frame = self.app.current_frame.copy()
                
                # Add timestamp
                cv2.putText(frame, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          (10, frame.shape[0] - 10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Encode as JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)  # ~30 FPS
    
    def start(self):
        """Start the web server in a background thread"""
        self.running = True
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Web interface started at http://localhost:{self.port}")
    
    def run_server(self):
        """Run the Flask server"""
        self.flask_app.run(host='0.0.0.0', port=self.port, threaded=True, debug=False)
    
    def stop(self):
        """Stop the web server"""
        self.running = False
        # Flask doesn't have a clean stop method, but the thread will die when main app exits