"""Email alert system for Cypher-Cam"""
import smtplib
import os
import json
import logging
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading
import queue
import cv2

logger = logging.getLogger(__name__)

class EmailAlertSystem:
    """Handles sending email alerts with snapshots"""
    
    def __init__(self, config_file="config/email_config.json"):
        self.config_file = config_file
        self.enabled = False
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = ""
        self.sender_password = ""
        self.recipient_email = ""
        self.alert_queue = queue.Queue()
        self.alert_cooldown = 60
        self.last_alert_time = 0
        self.load_config()
        
        self.running = True
        self.worker_thread = threading.Thread(target=self.process_alerts)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def load_config(self):
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.enabled = config.get('enabled', False)
                    self.smtp_server = config.get('smtp_server', 'smtp.gmail.com')
                    self.smtp_port = config.get('smtp_port', 587)
                    self.sender_email = config.get('sender_email', '')
                    self.sender_password = config.get('sender_password', '')
                    self.recipient_email = config.get('recipient_email', '')
                    self.alert_cooldown = config.get('alert_cooldown', 60)
                logger.info("Email configuration loaded")
        except Exception as e:
            logger.error(f"Failed to load email config: {e}")
    
    def save_config(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            config = {
                'enabled': self.enabled,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'sender_email': self.sender_email,
                'sender_password': self.sender_password,
                'recipient_email': self.recipient_email,
                'alert_cooldown': self.alert_cooldown
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            logger.info("Email configuration saved")
            return True
        except Exception as e:
            logger.error(f"Failed to save email config: {e}")
            return False
    
    def test_connection(self):
        if not self.sender_email or not self.sender_password:
            return False, "Email and password required"
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            return True, "Connection successful!"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def send_alert(self, alert_type, frame=None, message=""):
        if not self.enabled:
            return
        current_time = datetime.now().timestamp()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return
        self.alert_queue.put({
            'type': alert_type,
            'frame': frame.copy() if frame is not None else None,
            'message': message,
            'timestamp': current_time
        })
        self.last_alert_time = current_time
    
    def process_alerts(self):
        while self.running:
            try:
                alert = self.alert_queue.get(timeout=1)
                self._send_email_alert(alert)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
    
    def _send_email_alert(self, alert):
        try:
            msg = MIMEMultipart()
            msg['Subject'] = f"🔒 Cypher-Cam Alert: {alert['type'].upper()}"
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            timestamp = datetime.fromtimestamp(alert['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
            
            body = f"""
            <html>
            <body style="font-family: Arial; background: #0a0e14; color: #e6e9f0; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #1a1f2a; border-radius: 10px; padding: 20px; border-left: 4px solid #36d6e7;">
                    <h1 style="color: #36d6e7;">🔒 Cypher-Cam Alert</h1>
                    <div style="background: #2a3140; border-radius: 5px; padding: 15px;">
                        <p><strong>Type:</strong> {alert['type'].upper()}</p>
                        <p><strong>Time:</strong> {timestamp}</p>
                        <p><strong>Message:</strong> {alert['message']}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            if alert['frame'] is not None:
                temp_file = f"temp_alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(temp_file, cv2.cvtColor(alert['frame'], cv2.COLOR_RGB2BGR))
                with open(temp_file, 'rb') as f:
                    img = MIMEImage(f.read())
                    img.add_header('Content-Disposition', 'attachment', filename='snapshot.jpg')
                    msg.attach(img)
                os.remove(temp_file)
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            logger.info(f"Email alert sent: {alert['type']}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    def update_settings(self, enabled, sender_email, sender_password, recipient_email, 
                       smtp_server="smtp.gmail.com", smtp_port=587, cooldown=60):
        self.enabled = enabled
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.alert_cooldown = cooldown
        return self.save_config()
    
    def stop(self):
        self.running = False
        if self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2)