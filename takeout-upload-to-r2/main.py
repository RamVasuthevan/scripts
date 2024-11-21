import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv
from boto3.s3.transfer import TransferConfig, S3Transfer
from tqdm import tqdm
import time

class TqdmUpTo(tqdm):
    def update_to(self, bytes_amount):
        # Update the progress bar by the given number of bytes
        self.update(bytes_amount)

def upload_file(s3_client, file_path, bucket_name, r2_endpoint, retries=3):
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    # Configure transfer settings for multipart upload
    transfer_config = TransferConfig(
        multipart_threshold=1024 * 25,  # 25MB
        max_concurrency=5,  # Adjust concurrency as needed
        multipart_chunksize=1024 * 25,  # 25MB
        use_threads=True
    )

    # Initialize a progress bar
    with TqdmUpTo(total=file_size, unit='B', unit_scale=True, desc=file_name) as progress_bar:
        for attempt in range(retries):
            try:
                transfer = S3Transfer(s3_client, config=transfer_config)
                transfer.upload_file(file_path, bucket_name, file_name, callback=progress_bar.update_to)
                print(f"\nFile '{file_name}' uploaded to bucket '{bucket_name}' as '{file_name}'.")

                # Delete the file after successful upload
                os.remove(file_path)
                print(f"File '{file_name}' successfully deleted from local storage.")
                break  # Break the loop if upload succeeds

            except Exception as e:
                print(f"\nFailed to upload file '{file_name}' (attempt {attempt + 1}/{retries}): {e}")
                if attempt + 1 < retries:
                    print("Retrying...")
                    time.sleep(5)  # Wait for a bit before retrying
                else:
                    print("Max retries reached, moving to next file.")

def upload_folder_to_r2(folder_path, bucket_name, r2_endpoint):
    # Load environment variables from .env file
    load_dotenv()

    # Get the access keys from environment variables
    access_key_id = os.getenv('ACCESS_KEY_ID')
    secret_access_key = os.getenv('SECRET_ACCESS_KEY')

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
            },
            connect_timeout=60,
            read_timeout=60,
            max_pool_connections=10,
        )
    )

    processed_files = set()  # To keep track of already processed files

    while True:
        # Collect and sort the files in the folder alphabetically
        files_to_upload = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                if file_path not in processed_files:  # Only process new files
                    files_to_upload.append(file_path)

        # Sort the files alphabetically
        files_to_upload.sort()

        # Upload the files in alphabetical order
        for file_path in files_to_upload:
            upload_file(s3_client, file_path, bucket_name, r2_endpoint)
            processed_files.add(file_path)  # Mark the file as processed

        print("Waiting for new files...")
        time.sleep(10)  # Wait for 10 seconds before checking for new files

if __name__ == "__main__":
    # These values are specific to your setup
    BUCKET_NAME = 'google-photos-takeout-2024-08-05'
    FOLDER_PATH = 'data'  # Replace with your folder path
    R2_ENDPOINT = 'https://d07df139f817312af7e88eb0528dbdd0.r2.cloudflarestorage.com'

    upload_folder_to_r2(FOLDER_PATH, BUCKET_NAME, R2_ENDPOINT)
