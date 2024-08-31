import logging.handlers
import requests
import json
import sys
import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Define the log file name and path
LOG_FILE = os.path.join(logs_dir, f"streams_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging to write only to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fetch_streams_data(username):
    url = f"https://streams.place/{username}/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        exit(1)

def download_media(media_url, media_folder, file_name):
    try:
        response = requests.get(media_url)
        response.raise_for_status()
        file_path = os.path.join(media_folder, file_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        logger.info(f"Successfully downloaded: {file_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading media: {e}")
        exit(1)

def export_streams_json(username, data, output_dir):
    logger.info(f"Starting export for user: {username}")
    
    try:
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Save the JSON data to stream.json
        json_filename = os.path.join(output_dir, "stream.json")
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully exported JSON data to {json_filename}")

        # Download media files
        for item in data:
            for media in item.get('media', []):
                media_type = media['type']
                media_folder = os.path.join(output_dir, media_type)
                os.makedirs(media_folder, exist_ok=True)

                media_url = media['urlToFile']
                file_name = os.path.basename(media_url)
                download_media(media_url, media_folder, file_name)

        logger.info(f"Successfully exported all data and media for {username}")

    except IOError as e:
        logger.error(f"Error writing to file: {e}")
        exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python script_name.py <username> [output_directory]")
        sys.exit(1)

    username = sys.argv[1]
    if len(sys.argv) == 3:
        output_dir = sys.argv[2]
    else:
        output_dir = username  # Default to using the username as the directory name

    logger.info(f"Script started with username: {username} and output directory: {output_dir}")

    # Fetch data from the API
    data = fetch_streams_data(username)
    if data:
        export_streams_json(username, data, output_dir)
    else:
        logger.error("No data retrieved from API")
        exit(1)
        
    logger.info("Script execution completed")