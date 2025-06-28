import boto3
import os
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Optional
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class AWSHandler:
    def __init__(self):
        """Initialize AWS S3 client."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
                region_name=config.AWS_REGION
            )
            self.bucket_name = config.S3_BUCKET_NAME
            self._verify_credentials()
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {str(e)}")
            raise
    
    def _verify_credentials(self):
        """Verify AWS credentials and S3 access."""
        try:
            # Test credentials by listing buckets
            self.s3_client.list_buckets()
            logger.info("AWS credentials verified successfully")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            logger.error(f"AWS credentials error: {str(e)}")
            raise
    
    # def create_bucket_if_not_exists(self) -> bool:
    #     """Create S3 bucket if it doesn't exist."""
    #     try:
    #         # Check if bucket exists
    #         self.s3_client.head_bucket(Bucket=self.bucket_name)
    #         logger.info(f"Bucket '{self.bucket_name}' already exists")
    #         return True
            
    #     except ClientError as e:
    #         error_code = int(e.response['Error']['Code'])
            
    #         if error_code == 404:
    #             # Bucket doesn't exist, create it
    #             try:
    #                 if config.AWS_REGION == 'us-east-1':
    #                     # For us-east-1, don't specify LocationConstraint
    #                     self.s3_client.create_bucket(Bucket=self.bucket_name)
    #                 else:
    #                     self.s3_client.create_bucket(
    #                         Bucket=self.bucket_name,
    #                         CreateBucketConfiguration={'LocationConstraint': config.AWS_REGION}
    #                     )
                    
    #                 logger.info(f"Created bucket '{self.bucket_name}' successfully")
    #                 return True
                    
    #             except ClientError as create_error:
    #                 logger.error(f"Failed to create bucket: {str(create_error)}")
    #                 return False
    #         else:
    #             logger.error(f"Error checking bucket: {str(e)}")
    #             return False
    
    def upload_file(self, local_file_path: str, s3_key: Optional[str] = None) -> bool:
        """
        Upload a file to S3.
        
        Args:
            local_file_path: Path to local file
            s3_key: S3 key (filename) for the uploaded file
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(local_file_path):
            logger.error(f"Local file not found: {local_file_path}")
            return False
        
        # Use filename as S3 key if not provided
        if s3_key is None:
            s3_key = os.path.basename(local_file_path)
        
        try:
            # Upload file
            logger.info(f"Uploading {local_file_path} to s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                local_file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ContentType': 'video/mp4',
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            # Generate URL for the uploaded file
            url = f"https://{self.bucket_name}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key}"
            logger.info(f"Successfully uploaded to: {url}")
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to upload file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return False
    
    def upload_multiple_files(self, file_paths: List[str]) -> List[str]:
        """
        Upload multiple files to S3.
        
        Args:
            file_paths: List of local file paths
            
        Returns:
            List[str]: List of successfully uploaded S3 keys
        """
        uploaded_files = []
        
        for file_path in file_paths:
            filename = os.path.basename(file_path)
            
            if self.upload_file(file_path, filename):
                uploaded_files.append(filename)
            else:
                logger.error(f"Failed to upload: {filename}")
        
        logger.info(f"Successfully uploaded {len(uploaded_files)}/{len(file_paths)} files")
        return uploaded_files
    
    def list_bucket_contents(self) -> List[str]:
        """List all objects in the S3 bucket."""
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name)
            
            if 'Contents' in response:
                objects = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Found {len(objects)} objects in bucket")
                return objects
            else:
                logger.info("Bucket is empty")
                return []
                
        except ClientError as e:
            logger.error(f"Failed to list bucket contents: {str(e)}")
            return []
    
