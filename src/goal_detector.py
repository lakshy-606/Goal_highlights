import cv2
import numpy as np
import torch
from ultralytics import YOLO
from typing import List, Tuple, Optional
import logging
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FootballGoalDetector:
    def __init__(self):
        """Initialize the goal detector with YOLO model and detection parameters."""
        self.model = YOLO('yolov8n.pt')  # Use YOLOv8 nano for CPU efficiency
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        self.nms_threshold = config.NMS_THRESHOLD
        self.goal_indicators = []
        
    def detect_objects(self, frame: np.ndarray) -> dict:
        """Detect objects in a frame using YOLO."""
        results = self.model(frame, conf=self.confidence_threshold, iou=self.nms_threshold, verbose=False)
        
        detections = {
            'persons': [],
            'sports_ball': [],
            'all_objects': []
        }
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    detection = {
                        'class_id': class_id,
                        'confidence': confidence,
                        'bbox': [x1, y1, x2, y2],
                        'class_name': self.model.names[class_id]
                    }
                    
                    detections['all_objects'].append(detection)
                    
                    if class_id == 0:  # person
                        detections['persons'].append(detection)
                    elif class_id == 32:  # sports ball
                        detections['sports_ball'].append(detection)
                        
        return detections
    
    def detect_ball_in_goal_area(self, detections: dict, frame_shape: Tuple[int, int]) -> float:
        """Detect if ball is in potential goal area."""
        balls = detections.get('sports_ball', [])
        if not balls:
            return 0.0
            
        height, width = frame_shape[:2]
        goal_areas = [
            [0, height*0.3, width*0.2, height*0.7],      # Left goal area
            [width*0.8, height*0.3, width, height*0.7]   # Right goal area
        ]
        
        max_score = 0.0
        for ball in balls:
            ball_center_x = (ball['bbox'][0] + ball['bbox'][2]) / 2
            ball_center_y = (ball['bbox'][1] + ball['bbox'][3]) / 2
            
            for goal_area in goal_areas:
                if (goal_area[0] <= ball_center_x <= goal_area[2] and 
                    goal_area[1] <= ball_center_y <= goal_area[3]):
                    max_score = max(max_score, ball['confidence'])
                    
        return max_score
    
    def detect_celebrations(self, detections_history: List[dict]) -> List[float]:
        """Detect celebration patterns (increased movement, clustering of people)."""
        celebration_scores = []
        
        for detections in detections_history:
            score = 0.0
            persons = detections.get('persons', [])
            
            if len(persons) > 6:
                positions = [[p['bbox'][0] + p['bbox'][2]/2, p['bbox'][1] + p['bbox'][3]/2] 
                           for p in persons]
                
                if len(positions) >= 2:
                    positions = np.array(positions)
                    n_clusters = min(6, len(positions))
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    try:
                        clusters = kmeans.fit_predict(positions)
                        cluster_sizes = np.bincount(clusters)
                        max_cluster_size = np.max(cluster_sizes)
                        score += max_cluster_size / len(persons)
                    except:
                        score += 0.1
                        
            celebration_scores.append(score)
            
        return celebration_scores

    def calculate_goal_probability(self, 
                                 celebration_scores: List[float],
                                 ball_scores: List[float],
                                 detections_history: List[dict]) -> List[float]:
        """Calculate goal probability for each frame."""
        goal_probabilities = []
        
        celebration_scores = np.array(celebration_scores) if celebration_scores else np.array([0])
        ball_scores = np.array(ball_scores) if ball_scores else np.array([0])
        
        if np.max(celebration_scores) > 0:
            celebration_scores = celebration_scores / np.max(celebration_scores)
        if np.max(ball_scores) > 0:
            ball_scores = ball_scores / np.max(ball_scores)
            
        for i in range(len(detections_history)):
            celebration_score = celebration_scores[i] if i < len(celebration_scores) else 0
            ball_score = ball_scores[i] if i < len(ball_scores) else 0
            
            goal_prob = (
                0.35 * celebration_score + 
                0.65 * ball_score          
            )
            
            goal_probabilities.append(goal_prob)
            
        return goal_probabilities

    def find_goal_moments(self, goal_probabilities: List[float], fps: float) -> List[float]:
        """Find potential goal moments using peak detection."""
        if not goal_probabilities:
            return []
            
        probabilities = np.array(goal_probabilities)
        min_height = np.mean(probabilities) + 1.0 * np.std(probabilities)
        min_distance = int(fps * 20)
        
        peaks, properties = find_peaks(
            probabilities, 
            height=min_height,
            distance=min_distance,
            prominence=0.3
        )
        
        goal_timestamps = [peak / fps for peak in peaks]
        
        logger.info(f"Found {len(goal_timestamps)} potential goal moments at: {goal_timestamps}")
        return goal_timestamps

    def process_video(self, video_path: str) -> List[float]:
        """Process entire video and return goal timestamps."""
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"Processing video: {video_path}")
        logger.info(f"FPS: {fps}, Total frames: {total_frames}")
        
        frames = []
        detections_history = []
        ball_scores = []
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            height, width = frame.shape[:2]
            if width > 1280:
                scale = 1280 / width
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            frames.append(frame)
            
            detections = self.detect_objects(frame)
            detections_history.append(detections)
            
            ball_score = self.detect_ball_in_goal_area(detections, frame.shape)
            ball_scores.append(ball_score)
            
            if len(frames) > fps * 30:
                frames.pop(0)
                
            frame_count += 1
            if frame_count % 100 == 0:
                logger.info(f"Processed {frame_count}/{total_frames} frames")
                
        cap.release()

        logger.info("Detecting celebrations...")
        celebration_scores = self.detect_celebrations(detections_history)

        logger.info("Calculating goal probabilities...")
        goal_probabilities = self.calculate_goal_probability(
            celebration_scores, ball_scores, detections_history
        )

        goal_timestamps = self.find_goal_moments(goal_probabilities, fps)
        return goal_timestamps
