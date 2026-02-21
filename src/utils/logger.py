"""Logging configuration for the application"""
import logging
import os
from datetime import datetime

def setup_logger():
    """Configure logging for the entire application"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create filename with date
    log_filename = f"logs/cypher-cam_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)