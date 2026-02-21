"""Noise detection module for Cypher-Cam"""
import numpy as np
import queue
import sounddevice as sd
import logging

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
        self.audio_stream = None
        
    def start_listening(self):
        """Start audio stream for noise detection"""
        try:
            self.is_listening = True
            self.audio_stream = sd.InputStream(
                callback=self.audio_callback,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.duration)
            )
            self.audio_stream.start()
            logger.info("Noise detector started")
        except Exception as e:
            logger.error(f"Failed to start noise detector: {e}")
            self.is_listening = False
        
    def stop_listening(self):
        """Stop audio stream"""
        self.is_listening = False
        if self.audio_stream:
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
            try:
                _, volume = self.audio_queue.get_nowait()
                return volume
            except queue.Empty:
                return 0
        return 0