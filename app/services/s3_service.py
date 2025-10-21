"""
AWS S3 Service for BuildWise
Handles file uploads, downloads, and deletions in S3
"""
import os
import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

logger = logging.getLogger(__name__)


class S3Service:
    """Service for interacting with AWS S3"""
    
    _client = None
    _bucket_name = None
    
    @classmethod
    def _get_client(cls):
        """Initialize and return S3 client (singleton pattern)"""
        if cls._client is None:
            try:
                # Get credentials from environment
                aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
                aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
                aws_region = os.getenv("AWS_REGION", "eu-central-1")
                cls._bucket_name = os.getenv("S3_BUCKET_NAME")
                
                if not all([aws_access_key, aws_secret_key, cls._bucket_name]):
                    logger.error("S3 credentials not configured. Required: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET_NAME")
                    return None
                
                # Configure S3 client
                config = Config(
                    region_name=aws_region,
                    signature_version='s3v4',
                    retries={
                        'max_attempts': 3,
                        'mode': 'standard'
                    }
                )
                
                cls._client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    config=config
                )
                
                logger.info(f"S3 client initialized successfully for bucket: {cls._bucket_name}")
                
            except Exception as e:
                logger.error(f"Failed to initialize S3 client: {e}")
                cls._client = None
                
        return cls._client
    
    @classmethod
    def is_configured(cls) -> bool:
        """Check if S3 is properly configured"""
        return cls._get_client() is not None
    
    @classmethod
    async def upload_file(cls, file_content: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """
        Upload a file to S3
        
        Args:
            file_content: File content as bytes
            s3_key: S3 object key (path in bucket)
            content_type: MIME type of the file
            
        Returns:
            str: S3 object URL
            
        Raises:
            Exception: If upload fails
        """
        client = cls._get_client()
        if not client:
            raise Exception("S3 client not configured")
        
        try:
            # Upload file to S3
            client.put_object(
                Bucket=cls._bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256'  # Enable encryption at rest
            )
            
            # Generate public URL
            url = f"https://{cls._bucket_name}.s3.{os.getenv('AWS_REGION', 'eu-central-1')}.amazonaws.com/{s3_key}"
            
            logger.info(f"Successfully uploaded file to S3: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"S3 upload failed for {s3_key}: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
        except BotoCoreError as e:
            logger.error(f"BotoCore error during upload for {s3_key}: {e}")
            raise Exception(f"Failed to upload file to S3: {str(e)}")
    
    @classmethod
    async def download_file(cls, s3_key: str) -> bytes:
        """
        Download a file from S3
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            bytes: File content
            
        Raises:
            Exception: If download fails
        """
        client = cls._get_client()
        if not client:
            raise Exception("S3 client not configured")
        
        try:
            # Download file from S3
            response = client.get_object(
                Bucket=cls._bucket_name,
                Key=s3_key
            )
            
            file_content = response['Body'].read()
            logger.info(f"Successfully downloaded file from S3: {s3_key}")
            return file_content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File not found in S3: {s3_key}")
                raise Exception(f"File not found: {s3_key}")
            else:
                logger.error(f"S3 download failed for {s3_key}: {e}")
                raise Exception(f"Failed to download file from S3: {str(e)}")
        except BotoCoreError as e:
            logger.error(f"BotoCore error during download for {s3_key}: {e}")
            raise Exception(f"Failed to download file from S3: {str(e)}")
    
    @classmethod
    async def delete_file(cls, s3_key: str) -> bool:
        """
        Delete a file from S3
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            bool: True if successful, False otherwise
        """
        client = cls._get_client()
        if not client:
            logger.warning("S3 client not configured, cannot delete file")
            return False
        
        try:
            # Delete file from S3
            client.delete_object(
                Bucket=cls._bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Successfully deleted file from S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 deletion failed for {s3_key}: {e}")
            return False
        except BotoCoreError as e:
            logger.error(f"BotoCore error during deletion for {s3_key}: {e}")
            return False
    
    @classmethod
    def generate_presigned_url(cls, s3_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to a file
        
        Args:
            s3_key: S3 object key (path in bucket)
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL or None if failed
        """
        client = cls._get_client()
        if not client:
            logger.warning("S3 client not configured, cannot generate presigned URL")
            return None
        
        try:
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': cls._bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for {s3_key} (expires in {expiration}s)")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {s3_key}: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"BotoCore error generating presigned URL for {s3_key}: {e}")
            return None
    
    @classmethod
    def get_file_url(cls, s3_key: str) -> str:
        """
        Generate public S3 URL for a file
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            str: Public S3 URL
        """
        region = os.getenv('AWS_REGION', 'eu-central-1')
        return f"https://{cls._bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
    
    @classmethod
    async def file_exists(cls, s3_key: str) -> bool:
        """
        Check if a file exists in S3
        
        Args:
            s3_key: S3 object key (path in bucket)
            
        Returns:
            bool: True if file exists, False otherwise
        """
        client = cls._get_client()
        if not client:
            return False
        
        try:
            client.head_object(
                Bucket=cls._bucket_name,
                Key=s3_key
            )
            return True
        except ClientError:
            return False


# Export the service
__all__ = ['S3Service']

