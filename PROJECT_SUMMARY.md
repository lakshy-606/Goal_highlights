# Football Goal Detector - Project Summary

## Overview

This project implements an end-to-end pipeline for automatically detecting goals in football match videos and generating highlight clips. It combines object detection, heuristic scoring, and cloud integration into a single streamlined system.

## Key Features

### 1. Goal Detection System

* **Two-Stage Detection**: YOLOv8 for detecting people and balls, followed by temporal scoring to infer goals
* **Multi-Signal Scoring**: Uses celebration detection and ball-in-goal-area logic
* **Sliding Window Averaging**: Robust scoring over time to reduce false positives
* **CPU Optimized**: Runs on EC2 free-tier instances without GPU

### 2. Highlight Generation

* **Automatic Clipping**: Generates 20-second highlights around detected goals (10s before + 10s after)
* **Visual Marker**: Adds "⚽ GOAL! ⚽" overlay at goal moment
* **Efficient Encoding**: Compressed MP4 clips suitable for upload
* **Multiple Goals**: Handles several goals per video seamlessly

### 3. AWS Integration

* **S3 Upload**: Automatic uploading of highlight clips to AWS S3 bucket
* **Bucket Check**: Validates and creates bucket if needed
* **Secure**: Server-side AES256 encryption
* **Resilient**: Retry logic and error logging

### 4. Production Ready

* **Logging**: Detailed logging across all modules
* **Cleanup**: Temporary files removed post-processing
* **Environment Configurable**: Centralized config in `.env`
* **Testing Suite**: Includes unit and integration tests

## Technical Architecture

### Core Modules

1. **Goal Detector** (`src/goal_detector.py`)

   * YOLOv8 object detection
   * Celebration clustering with KMeans
   * Ball-in-goal-region heuristic
   * Sliding window scoring
   * Peak detection for timestamps

2. **Video Processor** (`src/video_processor.py`)

   * Highlight clipping with MoviePy
   * Overlay marker drawing
   * Video export and optimization

3. **AWS Handler** (`src/aws_handler.py`)

   * Uploads to S3
   * Bucket creation, access, and retry logic

4. **Main Pipeline** (`main.py`)

   * CLI entry point
   * Orchestrates end-to-end processing
   * Cleanup and logging

## Pipeline Logic (Goal Detection in Detail)

1. **Object Detection**:

   * YOLOv8 detects players (`class_id == 0`) and balls (`class_id == 32`)

2. **Ball Region Check**:

   * Ball coordinates are checked against fixed goal areas (left/right 20% of screen)

3. **Celebration Detection**:

   * Frame-wise clustering of player positions
   * High clustering (e.g., >6 players close together) indicates celebration

4. **Score Calculation**:

   * For each frame, combine ball presence (65%) and celebration (35%)

5. **Sliding Window Smoothing**:

   * 2-second rolling average smooths frame-wise scores to improve temporal reliability

6. **Peak Detection**:

   * `scipy.find_peaks()` applied on smoothed scores with parameters:

     * Height: mean + std
     * Distance: 20 seconds (to avoid multiple detections per goal)
     * Prominence: 0.3

7. **Timestamp Extraction**:

   * Detected peaks are converted to second-based timestamps

## File Structure

```
football_goal_detector/
├── main.py                   # Main pipeline script
├── config.py                 # Thresholds and constants
├── requirements.txt
├── src/
│   ├── goal_detector.py
│   ├── video_processor.py
│   └── aws_handler.py
├── utils/
│   └── video_utils.py
├── .env.example
├── README.md
├── test_pipeline.py
```

## Output Format

* File naming: `goal_highlight_{minute:02d}_{sequence}.mp4`
* Includes:

  * 10s before and after goal moment
  * Visual goal marker overlay
  * Compressed output

## AWS Setup

### Permissions Needed

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::football-highlights-bucket",
        "arn:aws:s3:::football-highlights-bucket/*"
      ]
    }
  ]
}
```

### Setup

1. Create IAM user with above permissions
2. Store access key/secret in `.env`
3. Bucket is auto-created if not found

## Deployment

### EC2 (Ubuntu)

```bash
# 1. Launch EC2 t2.micro
# 2. SSH in and setup:
sudo apt update && sudo apt install ffmpeg python3-pip
pip install -r requirements.txt
# 3. Run
python3 main.py path/to/video.mp4
```

## Evaluation Summary

✅ Accurate goal detection with multiple signals
✅ Overlay visual cue on clips
✅ 20s highlight clip generation
✅ Works on CPU
✅ Uploads to AWS S3
✅ Clean code and CLI interface
✅ Documented and tested

Ready for production deployment and demo. ✅
