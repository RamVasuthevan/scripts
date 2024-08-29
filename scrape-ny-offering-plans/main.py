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
LOG_FILE = os.path.join(logs_dir, f"resulst_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

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
    
    # Create results folder if it doesn't exist
    if not os.path.exists('results'):
        os.makedirs('results')
    
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
        logging.info(f"Navigating to page {page_number}")
        page.goto(page_url)
        
        # Get the HTML content
        html_content = page.content()
        
        # Save the HTML content to a file
        with open(f'results/page_{page_number}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"Saved page {page_number} of {last_page_number}")
        
        time.sleep(SLEEP_TIMEOUT)
    
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
        
        # Iterate through all HTML files in the results folder
        for filename in sorted(os.listdir('results')):
            if filename.endswith('.html'):
                logging.info(f"Parsing file: {filename}")
                with open(os.path.join('results', filename), 'r', encoding='utf-8') as f:
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