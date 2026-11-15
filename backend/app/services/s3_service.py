"""
AWS S3 Client and Storage Service.

Uses boto3 with a dedicated AWS profile (specified via AWS_PROFILE setting)
to avoid interfering with any default or existing credentials on the machine.
"""

from pathlib import Path
from typing import BinaryIO
import boto3
from botocore.exceptions import ClientError

from app.config import settings


class S3Service:
    """Manages artifact storage, checkpoints, and transparency records in AWS S3."""

    def __init__(self) -> None:
        self.profile = settings.AWS_PROFILE
        self.region = settings.AWS_REGION
        self.bucket_name = settings.S3_BUCKET_NAME
        self.endpoint_url = settings.S3_ENDPOINT_URL

        # Explicitly initialize session with the specified profile
        self.session = boto3.Session(
            profile_name=self.profile,
            region_name=self.region,
        )
        self.client = self.session.client(
            "s3",
            endpoint_url=self.endpoint_url,
        )

    def upload_file(self, local_path: Path | str, s3_key: str) -> str:
        """Upload a local file to S3 and return the S3 key."""
        local_path = Path(local_path)
        if not local_path.is_file():
            raise FileNotFoundError(f"File not found: {local_path}")

        self.client.upload_file(str(local_path), self.bucket_name, s3_key)
        return s3_key

    def download_file(self, s3_key: str, local_path: Path | str) -> Path:
        """Download a file from S3 to a local destination."""
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        self.client.download_file(self.bucket_name, s3_key, str(local_path))
        return local_path

    def upload_bytes(self, data: bytes, s3_key: str, content_type: str = "application/octet-stream") -> str:
        """Upload raw bytes directly to S3."""
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=s3_key,
            Body=data,
            ContentType=content_type,
        )
        return s3_key

    def get_bytes(self, s3_key: str) -> bytes:
        """Download raw bytes from an S3 object."""
        response = self.client.get_object(Bucket=self.bucket_name, Key=s3_key)
        return response["Body"].read()

    def delete_object(self, s3_key: str) -> None:
        """Delete an object from S3."""
        self.client.delete_object(Bucket=self.bucket_name, Key=s3_key)

    def ensure_bucket_exists(self) -> None:
        """Verify bucket exists or create it if required."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Create bucket in region
                create_args = {"Bucket": self.bucket_name}
                if self.region != "us-east-1":
                    create_args["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
                self.client.create_bucket(**create_args)
            else:
                raise


# Global instance
s3_service = S3Service()
