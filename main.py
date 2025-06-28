#!/usr/bin/env python3
"""
Football Goal Detector - Main Pipeline
Automatically detects goals in football videos and generates highlight clips.
"""

import os
import sys
import argparse
import logging
import tempfile
from pathlib import Path

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from goal_detector import FootballGoalDetector
from video_processor import VideoProcessor
from aws_handler import AWSHandler
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('goal_detector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FootballHighlightPipeline:
    def __init__(self):
        """Initialize the complete pipeline."""
        self.goal_detector = FootballGoalDetector()
        self.video_processor = VideoProcessor()
        self.aws_handler = AWSHandler()
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Pipeline initialized. Temp directory: {self.temp_dir}")
    
    def validate_input(self, video_path: str) -> bool:
        """Validate input video file."""
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return False
        
        # Check file size (warn if very large)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
        if file_size_mb > 1000:  # 1GB
            logger.warning(f"Large video file detected: {file_size_mb:.2f}MB")
            logger.warning("Processing may take considerable time on CPU-only environment")
        
        # Check video format
        valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        file_extension = Path(video_path).suffix.lower()
        
        if file_extension not in valid_extensions:
            logger.warning(f"Unusual video format: {file_extension}")
        
        logger.info(f"Input validation passed for: {video_path} ({file_size_mb:.2f}MB)")
        return True
    
    def process_video(self, video_path: str) -> dict:
        """
        Process video through the complete pipeline.
        
        Args:
            video_path: Path to input video file
            
        Returns:
            dict: Results containing goal timestamps and uploaded files
        """
        results = {
            'video_path': video_path,
            'goal_timestamps': [],
            'highlight_clips': [],
            'uploaded_files': [],
            'success': False
        }
        
        try:
            # Step 1: Validate input
            logger.info("=" * 50)
            logger.info("STARTING FOOTBALL GOAL DETECTION PIPELINE")
            logger.info("=" * 50)
            
            if not self.validate_input(video_path):
                return results
            
            
            # Step 2: Detect goals
            logger.info("Step 1/4: Detecting goals in video...")
            goal_timestamps = self.goal_detector.process_video(video_path)
            results['goal_timestamps'] = goal_timestamps
            
            if not goal_timestamps:
                logger.warning("No goals detected in the video")
                return results
            
            logger.info(f"Detected {len(goal_timestamps)} goal(s) at timestamps: {goal_timestamps}")
            
            # Step 3: Generate highlight clips
            logger.info("Step 2/4: Generating highlight clips...")
            highlight_clips = self.video_processor.create_multiple_highlights(
                video_path, 
                goal_timestamps, 
                self.temp_dir
            )
            results['highlight_clips'] = highlight_clips
            
            if not highlight_clips:
                logger.error("Failed to generate any highlight clips")
                return results
            
            # Step 4: Optimize clips for upload
            logger.info("Step 3/4: Optimizing clips for upload...")
            for clip_path in highlight_clips:
                self.video_processor.optimize_for_upload(clip_path)
            
            # Step 5: Upload to S3
            logger.info("Step 4/4: Uploading clips to AWS S3...")
            uploaded_files = self.aws_handler.upload_multiple_files(highlight_clips)
            results['uploaded_files'] = uploaded_files
            
            if uploaded_files:
                results['success'] = True
                logger.info("=" * 50)
                logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
                logger.info(f"Generated {len(highlight_clips)} highlight clips")
                logger.info(f"Uploaded {len(uploaded_files)} files to S3")
                logger.info("=" * 50)
            else:
                logger.error("Failed to upload clips to S3")
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return results
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp directory: {str(e)}")
    
    def print_results_summary(self, results: dict):
        """Print a summary of results."""
        print("\n" + "=" * 60)
        print("FOOTBALL GOAL DETECTION RESULTS")
        print("=" * 60)
        
        print(f"Input Video: {results['video_path']}")
        print(f"Goals Detected: {len(results['goal_timestamps'])}")
        
        if results['goal_timestamps']:
            print("\nGoal Timestamps:")
            for i, timestamp in enumerate(results['goal_timestamps'], 1):
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                print(f"  Goal {i}: {minutes:02d}:{seconds:02d} ({timestamp:.2f}s)")
        
        print(f"\nHighlight Clips Generated: {len(results['highlight_clips'])}")
        if results['highlight_clips']:
            for clip in results['highlight_clips']:
                print(f"  - {os.path.basename(clip)}")
        
        print(f"\nFiles Uploaded to S3: {len(results['uploaded_files'])}")
        if results['uploaded_files']:
            for file in results['uploaded_files']:
                print(f"  - {file}")
        
        print(f"\nPipeline Status: {'✅ SUCCESS' if results['success'] else '❌ FAILED'}")
        print("=" * 60)

def main():
    """Main function to run the pipeline."""
    parser = argparse.ArgumentParser(description='Football Goal Detection Pipeline')
    parser.add_argument('video_path', help='Path to input video file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-upload', action='store_true', help='Skip S3 upload (for testing)')
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        os.environ['DEBUG_MODE'] = 'True'
    
    # Initialize pipeline
    pipeline = FootballHighlightPipeline()
    
    try:
        # Process video
        results = pipeline.process_video(args.video_path)
        
        # Print results
        pipeline.print_results_summary(results)
        
        # Return appropriate exit code
        sys.exit(0 if results['success'] else 1)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
    finally:
        # Cleanup
        pipeline.cleanup()

if __name__ == "__main__":
    main() 