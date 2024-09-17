import re
import os
import time
import csv
import logging
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup

# Magic variables
SLEEP_TIMEOUT = 10  # Sleep timeout in seconds

# Create logs directory if it doesn't exist
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Define the log file name and path
LOG_FILE = os.path.join(logs_dir, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# Configure logging to write to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # Create pages folder if it doesn't exist
    if not os.path.exists('pages'):
        os.makedirs('pages')
    if not os.path.exists('pages/search'):
        os.makedirs('pages/search')
    if not os.path.exists('pages/buildings'):
        os.makedirs('pages/buildings')

    # Navigate to the initial page
    logging.info("Navigating to the initial page")
    page.goto("https://offeringplandatasearch.ag.ny.gov/REF/welcome.jsp")

    # Click the Search button
    logging.info("Clicking the Search button")
    page.get_by_role("button", name="Search").click()

    # Go to the last page to get the total number of pages
    logging.info("Getting the total number of pages")
    page.get_by_role("link", name="Last").click()
    url = page.url
    match = re.search(r'd-16544-p=(\d+)', url)
    if match:
        last_page_number = int(match.group(1))
        logging.info(f"Last page number: {last_page_number}")
    else:
        logging.error("Could not find the last page number in the URL")
        return

    # Go back to the first page
    logging.info("Returning to the first page")
    page.get_by_role("link", name="First").click()

    # Iterate through all pages
    for page_number in range(1, last_page_number + 1):
        page_url = f"https://offeringplandatasearch.ag.ny.gov/REF/search.action?d-16544-p={page_number}"
        logging.info(f"Navigating to page {page_number} of {last_page_number}")
        page.goto(page_url)
        page.wait_for_load_state('networkidle')

        # Get all the links in the first column
        links = page.query_selector_all('table#row td:first-child a')

        if not links:
            logging.warning(f"No links found on page {page_number}. This might be the last page.")
            break

        for link in links:
            try:
                id_number = link.inner_text().strip()
                logging.info(f"Processing link for ID: {id_number}")

                # Create a new tab
                new_page = context.new_page()
                
                # Go to the same URL as the main page
                new_page.goto(page_url)
                new_page.wait_for_load_state('networkidle')

                # Find and click the link in the new tab
                new_link = new_page.query_selector(f'table#row td:first-child a:text-is("{id_number}")')
                if new_link:
                    new_link.click()
                    new_page.wait_for_load_state('networkidle')

                    # Get the HTML content of the building page
                    building_html = new_page.content()

                    if building_html:
                        # Save the HTML content to a file
                        with open(f'pages/buildings/{id_number}.html', 'w', encoding='utf-8') as f:
                            f.write(building_html)
                        logging.info(f"Saved building page for ID: {id_number}")
                    else:
                        logging.error(f"Failed to retrieve building page for ID: {id_number}")
                else:
                    logging.error(f"Failed to find link for ID: {id_number} in the new tab")

                # Close the new tab
                new_page.close()

            except Exception as e:
                logging.error(f"Error processing ID {id_number}: {str(e)}")

        # Save the HTML content of the search page
        search_html = page.content()
        with open(f'pages/search/page_{page_number}.html', 'w', encoding='utf-8') as f:
            f.write(search_html)

        logging.info(f"Saved search page {page_number} of {last_page_number}")

        # Check if this is the last page
        next_button = page.query_selector('a:text("Next")')
        if not next_button:
            logging.info("Reached the last page. Stopping pagination.")
            break

    # Close the browser
    logging.info("Closing the browser")
    context.close()
    browser.close()

def parse_html_files_to_csv():
    # Create data folder if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    csv_file_path = 'data/offering_plans.csv'

    logging.info(f"Parsing HTML files and saving to CSV: {csv_file_path}")
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        header_written = False

        # Iterate through all HTML files in the pages/search folder
        for filename in sorted(os.listdir('pages/search')):
            if filename.endswith('.html'):
                logging.info(f"Parsing file: {filename}")
                with open(os.path.join('pages/search', filename), 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                    table = soup.find('table', {'id': 'row'})
                    if table:
                        # Write header row if not already written
                        if not header_written:
                            headers = [th.text.strip() for th in table.find_all('th')]
                            csv_writer.writerow(headers)
                            header_written = True

                        # Write data rows
                        for row in table.find_all('tr'):
                            columns = row.find_all('td')
                            if columns:
                                csv_writer.writerow([column.text.strip() for column in columns])

    logging.info(f"Data has been saved to {csv_file_path}")

# Run the Playwright script
logging.info("Starting the Playwright script")
with sync_playwright() as playwright:
    run(playwright)

# Parse the HTML files and save data to CSV
logging.info("Starting HTML parsing and CSV creation")
parse_html_files_to_csv()

logging.info("Script execution completed")