import os
import requests
import pickle
from bs4 import BeautifulSoup

# URL to download data from
url = "https://www.heritagetrust.on.ca/oha/search-results?handle=pow-form&backlinkslug=basic-search&fields%5Blimit%5D=20000"

# Directory to save the pickle file
save_directory = "data"
os.makedirs(save_directory, exist_ok=True)

# File path for the pickle file
pickle_file_path = os.path.join(save_directory, "search_results.pkl")

# Function to download and save the data
def download_and_save_data(url, file_path):
    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Get the content from the response
        data = response.content

        # Save the data using pickle
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)

        print(f"Data successfully downloaded and saved to {file_path}")

# Function to read the pickle file and extract the table
def extract_table_from_pickle(file_path):
    # Load the data from the pickle file
    with open(file_path, 'rb') as file:
        data = pickle.load(file)

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(data, 'html.parser')

    # Find the table within the HTML
    table = soup.find('tbody')  # Adjust the selector if needed

    # Check if a table was found
    if not table:
        print("No table found in the HTML content.")
        return

    # Extract table headers
    headers = [header.get_text(strip=True) for header in table.find_all('th')]

    # Extract table rows
    rows = []
    for row in table.find_all('tr'):
        # Find all cells in the row
        cells = row.find_all('td')
        if cells:
            # Extract "Property name" text and link
            property_name_tag = cells[0].find('a')  # Assuming the link is inside the first cell
            property_name_text = property_name_tag.get_text(strip=True) if property_name_tag else None
            property_name_link = property_name_tag['href'] if property_name_tag and 'href' in property_name_tag.attrs else None

            # Extract other columns
            street_address = cells[1].get_text(strip=True)
            municipality = cells[2].get_text(strip=True)
            construction_years = cells[3].get_text(strip=True)
            heritage_conservation_district = cells[4].get_text(strip=True)
            document_types = cells[5].get_text(strip=True)

            # Create a dictionary for each row
            row_dict = {
                "Property name text": property_name_text,
                "Property name link": property_name_link,
                "Street address": street_address,
                "Municipality": municipality,
                "Construction year(s)": construction_years,
                "Heritage Conservation District": heritage_conservation_district,
                "Document types": document_types
            }
            rows.append(row_dict)

    return rows

# Download and save the data
# download_and_save_data(url, pickle_file_path)

# Extract and display the table from the pickle file
extracted_data = extract_table_from_pickle(pickle_file_path)
