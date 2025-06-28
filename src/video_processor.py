import cv2
import numpy as np
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import os
import logging
from typing import List, Tuple
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self):
        """Initialize video processor."""
        self.output_format = config.OUTPUT_FORMAT
        self.output_quality = config.OUTPUT_QUALITY
        
    def extract_highlight_clip(self, 
                             video_path: str, 
                             goal_timestamp: float, 
                             output_path: str,
                             mark_goal_moment: bool = True) -> bool:
        """
        Extract highlight clip around goal moment.
        
        Args:
            video_path: Path to input video
            goal_timestamp: Timestamp of goal in seconds
            output_path: Path for output clip
            mark_goal_moment: Whether to add visual marker at goal moment
            
        Returns:
            bool: Success status
        """
        try:
            # Calculate clip boundaries
            start_time = max(0, goal_timestamp - config.PRE_GOAL_DURATION)
            end_time = goal_timestamp + config.POST_GOAL_DURATION
            
            logger.info(f"Extracting clip from {start_time:.2f}s to {end_time:.2f}s")
            
            # Load video clip
            with VideoFileClip(video_path) as video:
                # Check if end time exceeds video duration
                if end_time > video.duration:
                    end_time = video.duration
                    logger.warning(f"Adjusted end time to video duration: {end_time:.2f}s")
                
                # Extract subclip
                highlight_clip = video.subclip(start_time, end_time)
                
                # Add goal moment marker if requested
                if mark_goal_moment:
                    highlight_clip = self.add_goal_marker(
                        highlight_clip, 
                        goal_timestamp - start_time  # Relative timestamp in clip
                    )
                
                # Write output with compression
                highlight_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    preset='medium',
                    ffmpeg_params=['-crf', '23']  # Good quality with reasonable file size
                )
                
            logger.info(f"Successfully created highlight clip: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating highlight clip: {str(e)}")
            return False
    
    def add_goal_marker(self, video_clip, goal_moment_relative: float):
        """Add visual marker at the exact goal moment."""
        try:
            # Create text overlay for goal moment
            goal_text = TextClip(
                "⚽ GOAL! ⚽",
                fontsize=50,
                color='red',
                font='Arial-Bold',
                stroke_color='white',
                stroke_width=2
            ).set_position('center').set_duration(2)  # Show for 2 seconds
            
            # Position the text to appear at goal moment
            goal_text = goal_text.set_start(max(0, goal_moment_relative - 1))
            
            # Composite video with text overlay
            final_video = CompositeVideoClip([video_clip, goal_text])
            
            return final_video
            
        except Exception as e:
            logger.warning(f"Could not add goal marker: {str(e)}")
            return video_clip
    
    def get_video_info(self, video_path: str) -> dict:
        """Get video information."""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            return {
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'width': width,
                'height': height
            }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return {}
    
    def create_multiple_highlights(self, 
                                 video_path: str, 
                                 goal_timestamps: List[float], 
                                 output_dir: str) -> List[str]:
        """Create multiple highlight clips for all detected goals."""
        created_clips = []
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for i, goal_timestamp in enumerate(goal_timestamps):
            # Calculate minute of the goal for filename
            minute = int(goal_timestamp // 60)
            
            # Create output filename
            output_filename = f"{config.OUTPUT_PREFIX}{minute:02d}_{i+1}.{config.OUTPUT_FORMAT}"
            output_path = os.path.join(output_dir, output_filename)
            
            # Extract clip
            success = self.extract_highlight_clip(
                video_path, 
                goal_timestamp, 
                output_path,
                mark_goal_moment=True
            )
            
            if success:
                created_clips.append(output_path)
                logger.info(f"Created highlight clip {i+1}/{len(goal_timestamps)}: {output_filename}")
            else:
                logger.error(f"Failed to create highlight clip for goal at {goal_timestamp:.2f}s")
        
        return created_clips
    
    def optimize_for_upload(self, video_path: str) -> str:
        """Optimize video file for upload (compress if needed)."""
        try:
            # Check file size
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            
            if file_size_mb > 50:  # If larger than 50MB, compress more
                logger.info(f"Video file is {file_size_mb:.2f}MB, applying additional compression")
                
                # Create compressed version
                base_name = os.path.splitext(video_path)[0]
                compressed_path = f"{base_name}_compressed.mp4"
                
                with VideoFileClip(video_path) as video:
                    video.write_videofile(
                        compressed_path,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile='temp-audio.m4a',
                        remove_temp=True,
                        preset='fast',
                        ffmpeg_params=['-crf', '28']  # Higher compression
                    )
                
                # Replace original with compressed version
                os.replace(compressed_path, video_path)
                logger.info(f"Compressed video to {os.path.getsize(video_path) / (1024 * 1024):.2f}MB")
            
            return video_path
            
        except Exception as e:
            logger.error(f"Error optimizing video: {str(e)}")
            return video_path 