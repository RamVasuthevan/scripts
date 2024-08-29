import re
import os
import time
import csv
from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Create results folder if it doesn't exist
    if not os.path.exists('results'):
        os.makedirs('results')
    
    # Navigate to the initial page
    page.goto("https://offeringplandatasearch.ag.ny.gov/REF/welcome.jsp")
    
    # Click the Search button
    page.get_by_role("button", name="Search").click()
    
    # Go to the last page to get the total number of pages
    page.get_by_role("link", name="Last").click()
    url = page.url
    match = re.search(r'd-16544-p=(\d+)', url)
    if match:
        last_page_number = int(match.group(1))
        print(f"Last page number: {last_page_number}")
    else:
        print("Could not find the last page number in the URL")
        return
    
    # Go back to the first page
    page.get_by_role("link", name="First").click()
    
    # Iterate through all pages
    for page_number in range(1, last_page_number + 1):
        page_url = f"https://offeringplandatasearch.ag.ny.gov/REF/search.action?d-16544-p={page_number}"
        page.goto(page_url)
        
        # Get the HTML content
        html_content = page.content()
        
        # Save the HTML content to a file
        with open(f'results/page_{page_number}.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Saved page {page_number} of {last_page_number}")
        
        time.sleep(10)  # Sleep for 10 seconds between requests
        
        if page_number == 10:  # Break after 10 pages
            break  # Remove this line when you want to process all pages
    
    # Close the browser
    context.close()
    browser.close()

def parse_html_files_to_csv():
    # Create data folder if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    csv_file_path = 'data/offering_plans.csv'
    
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        header_written = False
        
        # Iterate through all HTML files in the results folder
        for filename in sorted(os.listdir('results')):
            if filename.endswith('.html'):
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
    
    print(f"Data has been saved to {csv_file_path}")

# Run the Playwright script
with sync_playwright() as playwright:
    run(playwright)

# Parse the HTML files and save data to CSV
parse_html_files_to_csv()