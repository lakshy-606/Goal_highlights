import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_ACCESS_KEY_ID = 'AKIA5GCWT4SCKQT4PPO2'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'football-highlights-bucket-02') #football-highlights-bucket-01
PAT = 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
# Video Processing Configuration
HIGHLIGHT_DURATION = 20  # Total duration in seconds
PRE_GOAL_DURATION = 10   # Seconds before goal
POST_GOAL_DURATION = 10  # Seconds after goal

# Goal Detection Configuration
CONFIDENCE_THRESHOLD = 0.6
NMS_THRESHOLD = 0.3
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

# Debug Configuration
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
SAVE_INTERMEDIATE_FRAMES = DEBUG_MODE 
