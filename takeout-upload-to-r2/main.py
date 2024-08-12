import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig, S3Transfer
from tqdm import tqdm

class TqdmUpTo(tqdm):
    def update_to(self, bytes_amount):
        # Update the progress bar by the given number of bytes
        self.update(bytes_amount)

def upload_to_r2(bucket_name, file_name, r2_endpoint):
    # Load environment variables from .env file
    load_dotenv()

    # Get the access keys from environment variables
    access_key_id = os.getenv('ACCESS_KEY_ID')
    secret_access_key = os.getenv('SECRET_ACCESS_KEY')

    # The file path is relative to where the script is run
    file_path = os.path.join(os.getcwd(), file_name)

    # Configure the S3 client with R2 details
    s3_client = boto3.client(
        's3',
        endpoint_url=r2_endpoint,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(
            signature_version='s3v4',
            retries={
                'max_attempts': 10,
                'mode': 'standard'
            }
        )
    )

    # Configure transfer settings for multipart upload
    transfer_config = TransferConfig(
        multipart_threshold=1024 * 25,  # 25MB
        max_concurrency=5,  # Adjust concurrency as needed
        multipart_chunksize=1024 * 25,  # 25MB
        use_threads=True
    )

    file_size = os.path.getsize(file_path)

    # Initialize a progress bar
    with TqdmUpTo(total=file_size, unit='B', unit_scale=True, desc=file_name) as progress_bar:
        # Upload the file using multipart upload
        try:
            transfer = S3Transfer(s3_client, config=transfer_config)
            transfer.upload_file(file_path, bucket_name, file_name, callback=progress_bar.update_to)
            print(f"\nFile '{file_name}' uploaded to bucket '{bucket_name}' as '{file_name}'.")
        except Exception as e:
            print(f"\nFailed to upload file: {e}")

if __name__ == "__main__":
    # These values are specific to your setup
    BUCKET_NAME = 'test'
    FILE_NAME = 'takeout-20240806T032531Z-001.zip'
    R2_ENDPOINT = 'https://d07df139f817312af7e88eb0528dbdd0.r2.cloudflarestorage.com'

    upload_to_r2(BUCKET_NAME, FILE_NAME, R2_ENDPOINT)
