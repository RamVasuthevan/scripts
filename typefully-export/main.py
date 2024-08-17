import os
import requests
import json
from dotenv import load_dotenv
import logging

LOG_FILE: str = "export_processing.log"

# Configure logging to write only to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE)
    ]
)

# Load environment variables
load_dotenv()

# Get API token from environment variable
API_TOKEN = os.getenv('TYPEFULLY_API_TOKEN')

# Base URL for the API
BASE_URL = 'https://api.typefully.com/v1'

# Headers for authentication
headers = {
    'X-API-KEY': f'Bearer {API_TOKEN}'
}

# Folder to store the JSON files
DATA_FOLDER = 'data'

def get_api_data(endpoint):
    """
    Fetch data from the specified API endpoint
    """
    url = f'{BASE_URL}{endpoint}'
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching data from {endpoint}: {str(e)}")
        return None

def write_to_json(data, filename):
    """
    Write data to a JSON file in the specified folder
    """
    # Create the folder if it doesn't exist
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    # Full path for the file
    file_path = os.path.join(DATA_FOLDER, filename)
    
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data written to {file_path}")
    except IOError as e:
        logging.error(f"Error writing to {file_path}: {str(e)}")

def main():
    # Endpoints to fetch data from
    endpoints = {
        'recently_scheduled': '/drafts/recently-scheduled/',
        'recently_published': '/drafts/recently-published/',
        'latest_notifications': '/notifications/'
    }

    # Fetch data from each endpoint and write to JSON files
    for name, endpoint in endpoints.items():
        logging.info(f"Fetching data from {endpoint}")
        data = get_api_data(endpoint)
        if data is not None:
            write_to_json(data, f'{name}.json')
        else:
            logging.warning(f"No data retrieved for {name}. Writing empty JSON object.")
            write_to_json({}, f'{name}.json')  # Write an empty JSON object

if __name__ == "__main__":
    main()