import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from fastapi import HTTPException
from starlette import status
from typing import BinaryIO, List

from app.log import logger
from app.config import Settings

settings = Settings()


class S3Client:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name
        self.region_name = settings.default_region

        # Multipart upload configuration
        self.transfer_config = TransferConfig(
            multipart_threshold=5 * 1024 * 1024,   # Use multipart upload for files larger than 5 MB
            multipart_chunksize=10 * 1024 * 1024,  # Each part will be 10 MB in size
            max_concurrency=4,                     # Number of parallel threads for uploading parts
            use_threads=True                       # Enable multithreading for faster uploads
        )

        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.client = boto3.client(
                "s3",
                region_name=self.region_name,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        else:
            self.client = boto3.client(
                region_name=settings.default_region,
            )

        # Create bucket if it does not exist
        self.create_bucket_if_not_exists()

        cors_configuration = {
            "CORSRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["PUT", "GET", "POST"],
                    "AllowedOrigins": ["*"],
                    "ExposeHeaders": ["ETag"],
                    "MaxAgeSeconds": 3000
                }
            ]
        }
        self.client.put_bucket_cors(
            Bucket=self.bucket_name,
            CORSConfiguration=cors_configuration
        )


    def check_file_exists_on_s3(self, file_path: str) -> bool:
        """
        Check if a file exists in the S3 bucket.

        :param file_path: Path (key) of the file in the S3 bucket.
        :return: True if the file exists, False if not.
        """
        logger.info(f"check exits file in S3: {file_path}")
        try:
            # Use head_object to check if the file exists without downloading it.
            self.client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            # Extract the error code from the AWS response
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                # File does not exist in S3
                logger.error(f"File does not exist in S3: {e}")
                return False
            else:
                # Any other error (e.g., permissions, network) will be logged
                logger.error(f"Error checking file on S3: {e}")
                return False


    def create_bucket_if_not_exists(self):
        try:
            existing_buckets = self.client.list_buckets()
            buckets = [b['Name'] for b in existing_buckets.get('Buckets', [])]
            if self.bucket_name not in buckets:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Bucket '{self.bucket_name}' created.")
            else:
                logger.info(f"Bucket '{self.bucket_name}' already exists.")
        except ClientError as e:
            logger.error(f"Error checking/creating bucket: {e}")

    def upload_file_bytes(self, data, s3_key):
        try:
            self.client.upload_fileobj(
                Fileobj=data, 
                Bucket=self.bucket_name, 
                Key=s3_key,
                Config=self.transfer_config
            )
            logger.info(f"File uploaded to S3: {s3_key}")
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file to S3")

    
    def upload_file(self, file_path: str, s3_key: str):
        try:
            with open(file_path, "rb") as file:
                self.client.upload_fileobj(file, self.bucket_name, s3_key)
                logger.info(f"File uploaded to S3: {s3_key}")
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload file to S3")
        

    def upload_zip_buffer(
        self,
        zip_buffer: bytes,
        s3_key: str,
    ):
        """
        Upload zip data (bytes / BytesIO) to S3
        """
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=zip_buffer,
                ContentType="application/zip",
            )

            logger.info(f"Zip file uploaded to S3: {s3_key}")

        except ClientError as e:
            logger.error(f"Failed to upload zip to S3: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to upload zip file to S3",
            )
        

    def download_file(self, file_path: str, local_path: str):
        try:
            self.client.download_file(self.bucket_name, file_path, local_path)
            logger.info(f"File downloaded from S3: {file_path}")
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to download file from S3")


    def download_fileobj(self, file_key: str, file_obj: BinaryIO) -> None:
        """
        Download a file from S3 and write its content to a file-like object.

        Args:
            file_key (str): The key (path) of the file in the S3 bucket.
            file_obj (BinaryIO): A writable file-like object, e.g., BytesIO or a real file.

        Raises:
            RuntimeError: If download fails.
        """
        try:
            self.client.download_fileobj(Bucket=self.bucket_name, Key=file_key, Fileobj=file_obj)
        except ClientError as e:
            raise RuntimeError(f"Failed to download {file_key} from bucket {self.bucket_name}: {e}")


    def read_file(self, file_path: str, decode: str = "") -> str:
        try:
            obj = self.client.get_object(Bucket=self.bucket_name, Key=file_path)
            if decode:
                content = obj["Body"].read().decode(decode)
            else:
                content = obj["Body"].read()
            logger.info(f"File read from S3: {file_path}")
            return content
        except ClientError as e:
            logger.error(f"Failed to read file from S3: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read file from S3")
    

    def list_files(self, prefix: str) -> List[str]:
        """List all files (not folders) under a prefix"""
        try:
            s3 = self.client
            paginator = s3.get_paginator("list_objects_v2")
            keys: List[str] = []

            for page in paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=prefix,
            ):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    if not key.endswith("/"):
                        keys.append(key)

            return keys

        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to list files from S3",
            )

    
    def generate_presigned_url(self, file_path: str, client_method='get_object', expires_in=3600, content_type=""):  # noqa
        try:
            params = {"Bucket": self.bucket_name, "Key": file_path}
            if content_type:
                params["ContentType"] = content_type
            url = self.client.generate_presigned_url(ClientMethod=client_method, Params=params, ExpiresIn=expires_in)
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to generate presigned URL")


    def delete_file(self, s3_key: str):
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Deleted file s3://{self.bucket_name}/{s3_key}")
        except Exception as e:
            logger.error(f"Failed to delete {s3_key}: {e}")
