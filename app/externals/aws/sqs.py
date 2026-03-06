import boto3
import botocore
from typing import Optional, List, Dict

from app.log import logger
from app.config import Settings

settings = Settings()


class SQSClient:
    def __init__(self, sqs_queue_url: str = settings.outbound_queue_url) -> None:
        self.queue_url = sqs_queue_url
        self.is_fifo = self.queue_url.endswith(".fifo")
        
        # Log configuration for debugging
        logger.info("Initializing SQS client with:")
        logger.info(f"- Region: {settings.default_region}")
        logger.info(f"- Queue URL: {self.queue_url}")
        logger.info(f"- Access Key ID: {settings.aws_access_key_id[:4]}...{settings.aws_access_key_id[-4:] if settings.aws_access_key_id else 'None'}")
        
        try:
            self.sqs = boto3.client(
                "sqs",
                region_name=settings.default_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )

            # Test credentials by getting queue attributes
            self.sqs.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=['QueueArn']
            )
            logger.info("Successfully validated SQS credentials and queue access")
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            logger.error(f"Failed to initialize SQS client: {error_code} - {error_message}")
            raise


    def send_message(self, body: str, group_id: Optional[str] = None, dedup_id: Optional[str] = None) -> Optional[str]:
        params = {
            "QueueUrl": self.queue_url,
            "MessageBody": body
        }
        if self.is_fifo:
            if not group_id:
                raise ValueError("FIFO queue requires MessageGroupId.")
            params["MessageGroupId"] = group_id
            if dedup_id:
                params["MessageDeduplicationId"] = dedup_id

        try:
            response = self.sqs.send_message(**params)
            return response.get("MessageId")
        except botocore.exceptions.BotoCoreError as e:
            logger.error("Failed to send message", exc_info=e)
            return None

    def receive_messages(self, max_messages: int = 1, wait_time: int = 0) -> List[Dict]:
        try:
            logger.info(f"Attempting to receive messages from queue: {self.queue_url}")
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time
            )
            return response.get("Messages", [])
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            logger.error(f"SQS receive_message failed with error code: {error_code}, message: {error_message}", exc_info=e)
            return []
        except botocore.exceptions.BotoCoreError as e:
            logger.error("Failed to receive messages", exc_info=e)
            return []

    def delete_message(self, receipt_handle: str) -> bool:
        try:
            self.sqs.delete_message(QueueUrl=self.queue_url, ReceiptHandle=receipt_handle)
            return True
        except botocore.exceptions.BotoCoreError as e:
            logger.error("Failed to delete message", exc_info=e)
            return False
