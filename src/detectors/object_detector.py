"""Object detection module using YOLO or OpenCV's DNN"""
import cv2
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)

class ObjectDetector:
    """Detects people and objects using deep learning"""
    
    def __init__(self, confidence_threshold=0.5):
        self.confidence_threshold = confidence_threshold
        self.net = None
        self.classes = []
        self.output_layers = []
        
        # Load the model
        self.load_model()
    
    def load_model(self):
        """Load pre-trained YOLO model"""
        try:
            # Use OpenCV's pre-trained Caffe model for people detection
            # This is lighter and works well for people
            prototxt = "models/MobileNetSSD_deploy.prototxt"
            caffemodel = "models/MobileNetSSD_deploy.caffemodel"
            
            # Check if we need to download the model files
            if not os.path.exists(prototxt) or not os.path.exists(caffemodel):
                logger.info("Model files not found. Using OpenCV's default HOG detector instead.")
                # Fallback to HOG detector (simpler, CPU-only)
                self.use_hog = True
                self.hog = cv2.HOGDescriptor()
                self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
                return
            
            # Load the network
            self.net = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
            self.use_hog = False
            logger.info("Object detector model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.info("Falling back to HOG detector")
            self.use_hog = True
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    
    def detect(self, frame):
        """Detect objects in frame"""
        objects = []
        
        if self.use_hog:
            # Use HOG detector (good for people, faster)
            return self.detect_hog(frame)
        else:
            # Use deep learning model (more accurate, supports multiple classes)
            return self.detect_dnn(frame)
    
    def detect_hog(self, frame):
        """Detect people using HOG detector"""
        try:
            # Detect people
            (rects, _) = self.hog.detectMultiScale(
                frame, 
                winStride=(4, 4),
                padding=(8, 8),
                scale=1.05
            )
            
            objects = []
            for (x, y, w, h) in rects:
                # Draw bounding box
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                
                # Add label
                cv2.putText(frame, "Person", (x, y-5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                
                objects.append({
                    'class': 'person',
                    'confidence': 1.0,
                    'box': (x, y, w, h)
                })
            
            return objects, frame
            
        except Exception as e:
            logger.error(f"HOG detection error: {e}")
            return [], frame
    
    def detect_dnn(self, frame):
        """Detect objects using deep learning model"""
        try:
            # Prepare image for network
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 
                0.007843, 
                (300, 300), 
                127.5
            )
            
            # Pass through network
            self.net.setInput(blob)
            detections = self.net.forward()
            
            objects = []
            h, w = frame.shape[:2]
            
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > self.confidence_threshold:
                    class_id = int(detections[0, 0, i, 1])
                    
                    # COCO class names (simplified)
                    class_names = ['background', 'aeroplane', 'bicycle', 'bird', 'boat',
                                 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable',
                                 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep',
                                 'sofa', 'train', 'tvmonitor']
                    
                    if class_id < len(class_names):
                        label = class_names[class_id]
                        
                        # Get box coordinates
                        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (x1, y1, x2, y2) = box.astype("int")
                        
                        # Draw bounding box
                        color = self.get_color(class_id)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Add label
                        label_text = f"{label}: {confidence:.2f}"
                        cv2.putText(frame, label_text, (x1, y1-5),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
                        objects.append({
                            'class': label,
                            'confidence': confidence,
                            'box': (x1, y1, x2-x1, y2-y1)
                        })
            
            return objects, frame
            
        except Exception as e:
            logger.error(f"DNN detection error: {e}")
            return [], frame
    
    def get_color(self, class_id):
        """Get color based on class"""
        colors = {
            1: (255, 0, 0),    # aeroplane - blue
            2: (0, 255, 0),    # bicycle - green
            3: (0, 255, 255),  # bird - yellow
            4: (255, 0, 255),  # boat - magenta
            5: (255, 255, 0),  # bottle - cyan
            6: (128, 0, 0),    # bus - maroon
            7: (0, 128, 0),    # car - dark green
            8: (0, 0, 255),    # cat - red
            9: (255, 165, 0),  # chair - orange
            10: (128, 128, 0), # cow - olive
            15: (255, 0, 0),   # person - blue
        }
        return colors.get(class_id, (255, 255, 255))
    
    def count_people(self, objects):
        """Count number of people detected"""
        return sum(1 for obj in objects if obj['class'] == 'person')