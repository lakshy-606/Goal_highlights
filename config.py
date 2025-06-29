import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration

# Video Processing Configuration
HIGHLIGHT_DURATION = 20  # Total duration in seconds
PRE_GOAL_DURATION = 10   # Seconds before goal
POST_GOAL_DURATION = 10  # Seconds after goal

# Goal Detection Configuration
CONFIDENCE_THRESHOLD = 0.45
NMS_THRESHOLD = 0.4
GOAL_DETECTION_KEYWORDS = [
    'goal', 'celebration', 'net', 'keeper', 'score',
    'ball in net', 'goalkeeper beaten'
]

# Model Configuration
MODEL_INPUT_SIZE = (640, 640)
BATCH_SIZE = 1

# Output Configuration
OUTPUT_FORMAT = 'mp4'
OUTPUT_QUALITY = 'medium'
OUTPUT_PREFIX = 'goal_highlight_'


