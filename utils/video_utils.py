import cv2
import numpy as np
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def get_video_properties(video_path: str) -> dict:
    """ Get comprehensive video properties. """
    try:
        cap = cv2.VideoCapture(video_path)
        
        properties = {
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'duration': 0,
            'file_size_mb': 0,
            'codec': 'unknown'
        }
        
        # Calculate duration
        if properties['fps'] > 0:
            properties['duration'] = properties['frame_count'] / properties['fps']
        
        # Get file size
        if os.path.exists(video_path):
            properties['file_size_mb'] = os.path.getsize(video_path) / (1024 * 1024)
        
        cap.release()
        
        logger.info(f"Video properties: {properties}")
        return properties
        
    except Exception as e:
        logger.error(f"Error getting video properties: {str(e)}")
        return {}

def resize_video_frame(frame: np.ndarray, max_width: int = 1280) -> np.ndarray:
    """Resize video frame while maintaining aspect ratio."""
    height, width = frame.shape[:2]
    
    if width > max_width:
        scale = max_width / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height))
    
    return frame

def extract_frames_at_timestamps(video_path: str, timestamps: list, output_dir: str = "frames") -> list:
    """Extract frames at specific timestamps."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    extracted_frames = []
    
    for i, timestamp in enumerate(timestamps):
        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(output_dir, f"frame_{i}_{timestamp:.2f}s.jpg")
            cv2.imwrite(frame_path, frame)
            extracted_frames.append(frame_path)
            logger.info(f"Extracted frame at {timestamp:.2f}s")
    
    cap.release()
    return extracted_frames

def validate_video_file(video_path: str) -> bool:
    """Validate if video file can be opened and processed."""
    try:
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            logger.error(f"Cannot open video file: {video_path}")
            return False
        
        # Try to read first frame
        ret, frame = cap.read()
        if not ret:
            logger.error(f"Cannot read frames from video: {video_path}")
            cap.release()
            return False
        
        # Check basic properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        if fps <= 0 or frame_count <= 0:
            logger.error(f"Invalid video properties: fps={fps}, frames={frame_count}")
            cap.release()
            return False
        
        cap.release()
        return True
        
    except Exception as e:
        logger.error(f"Video validation error: {str(e)}")
        return False

def calculate_optimal_resolution(original_width: int, original_height: int, target_width: int = 1280) -> Tuple[int, int]:
    """Calculate optimal resolution for processing while maintaining aspect ratio."""
    if original_width <= target_width:
        return original_width, original_height
    
    scale = target_width / original_width
    new_width = target_width
    new_height = int(original_height * scale)
    
    # Ensure dimensions are even (required for some codecs)
    new_width = new_width if new_width % 2 == 0 else new_width - 1
    new_height = new_height if new_height % 2 == 0 else new_height - 1
    
    return new_width, new_height 