import requests

# File containing the list of pages
watchlist_file = 'watchlist.txt'

# URL of the Wikipedia API
api_url = "https://en.wikipedia.org/w/api.php"

# Text to search for
search_text = "pqasb.pqarchiver.com/"

# Function to fetch page content
def fetch_page_content(page_title):
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": page_title,
        "rvslots": "main",
        "rvprop": "content",
        "format": "json"
    }
    response = requests.get(api_url, params=params)
    data = response.json()
    pages = data["query"]["pages"]
    for page_id in pages:
        if "revisions" in pages[page_id]:
            return pages[page_id]["revisions"][0]["slots"]["main"]["*"]
    return ""

# Read the list of pages from the file
with open(watchlist_file, 'r') as file:
    pages = [line.strip() for line in file.readlines()]

# Search for the text in each page
matching_pages = []

for page in pages:
    content = fetch_page_content(page)
    if search_text in content:
        matching_pages.append(page)

# Print matching pages
for title in matching_pages:
    print(f'Matching page: {title}')
