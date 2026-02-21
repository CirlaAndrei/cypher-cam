"""Audio recording module for Cypher-Cam"""
import numpy as np
import os
import wave
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Handles audio recording"""
    
    def __init__(self, output_dir="recordings"):
        self.output_dir = output_dir
        self.recording = False
        self.frames = []
        self.sample_rate = 44100
        
        # Create recordings directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def start_recording(self):
        """Start recording sound"""
        self.recording = True
        self.frames = []
        logger.info("Audio recording started")
        
    def stop_recording(self):
        """Stop recording and save file"""
        self.recording = False
        if self.frames:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.output_dir}/audio_{timestamp}.wav"
                
                # Concatenate all audio frames
                audio_data = np.concatenate(self.frames, axis=0)
                
                # Convert to int16 if needed
                if audio_data.dtype != np.int16:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # Save as WAV file
                with wave.open(filename, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 2 bytes for int16
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(audio_data.tobytes())
                
                logger.info(f"Audio saved: {filename}")
                return filename
                
            except Exception as e:
                logger.error(f"Error saving audio: {e}")
                return None
        return None
    
    def add_frame(self, audio_data):
        """Add audio frame to recording"""
        if self.recording:
            self.frames.append(audio_data.copy())