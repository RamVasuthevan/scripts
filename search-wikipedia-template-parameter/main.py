import requests

def get_pages_using_template(template_name, limit=500):
    # Base URL for Wikipedia API
    url = "https://en.wikipedia.org/w/api.php"
    
    # Parameters for the API query
    params = {
        "action": "query",
        "format": "json",
        "list": "embeddedin",
        "eititle": f"Template:{template_name}",
        "eilimit": limit,
        "continue": "",
    }
    
    pages = []
    while True:
        response = requests.get(url, params=params)
        data = response.json()
        
        # Add page titles to the list
        pages.extend([item['title'] for item in data['query']['embeddedin']])
        
        # Check if there's a continuation token
        if "continue" in data:
            params.update(data["continue"])
        else:
            break
    
    return pages

def write_links_to_file(pages, filename="results.txt"):
    # Open a file to write the links
    with open(filename, "w", encoding="utf-8") as file:
        for page in pages:
            # Format the page title into a URL
            url = f"https://en.wikipedia.org/wiki/{page.replace(' ', '_')}"
            # Write the URL to the file
            file.write(url + "\n")

if __name__ == "__main__":
    template_name = "Infobox political division"
    pages = get_pages_using_template(template_name)
    
    # Write the list of pages to a text file
    write_links_to_file(pages)
