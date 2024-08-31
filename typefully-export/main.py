import os
import requests
import json
from dotenv import load_dotenv
import logging
from requests.exceptions import HTTPError

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
        response.raise_for_status()
        data = response.json()
        if not data:
            logging.error(f"Empty response received from {endpoint}")
            exit(1)
    except HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching data from {endpoint}: {http_err}")
        exit(1)
    except Exception as err:
        logging.error(f"An error occurred while fetching data from {endpoint}: {err}")
        exit(1)

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
    # Check if API token exists
    if not API_TOKEN:
        logging.error("TYPEFULLY_API_TOKEN is not set. Please set the environment variable.")
        exit(1)

    # Endpoints to fetch data from
    endpoints = {
        'recently_scheduled': '/drafts/recently-scheduled/',
        'recently_published': '/drafts/recently-published/',
        'latest_notifications': '/notifications/'
    }

    # Flag to check if any data was retrieved
    data_retrieved = False

    # Fetch data from each endpoint and write to JSON files
    for name, endpoint in endpoints.items():
        logging.info(f"Fetching data from {endpoint}")
        data = get_api_data(endpoint)
        if data is not None:
            if data:  # Check if data is not empty
                write_to_json(data, f'{name}.json')
                data_retrieved = True
            else:
                logging.warning(f"No data retrieved for {name}. Writing empty JSON object.")
                write_to_json({}, f'{name}.json')  # Write an empty JSON object
        else:
            logging.error(f"Failed to retrieve data for {name}. Skipping this endpoint.")

    if not data_retrieved:
        logging.warning("No data was retrieved from any endpoint. Please check your API token and endpoints.")

if __name__ == "__main__":
    main()