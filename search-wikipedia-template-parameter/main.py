import requests

def get_pages_using_template(template_name, limit=500):
    """Fetch all pages that use a given Wikipedia template."""
    url = "https://en.wikipedia.org/w/api.php"
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
        
        # Check for continuation
        if "continue" in data:
            params.update(data["continue"])
        else:
            break
    
    return pages

def page_contains_parameter(page_title, parameter_name):
    """Check if a given page contains a specific parameter in the template."""
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": page_title,
        "rvslots": "main",
        "rvprop": "content",
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Extract page content
    page = next(iter(data['query']['pages'].values()))
    content = page.get('revisions', [{}])[0].get('*', '')

    # Check if the parameter is present in the template
    return f"| {parameter_name} =" in content

def filter_pages_without_parameter(pages, parameter_name):
    """Filter out pages that contain a specific parameter."""
    filtered_pages = []
    for page in pages:
        if not page_contains_parameter(page, parameter_name):
            filtered_pages.append(page)
    return filtered_pages

def write_links_to_file(pages, filename="filtered_pages.txt"):
    """Write the filtered pages' links to a text file."""
    with open(filename, "w", encoding="utf-8") as file:
        for page in pages:
            # Format the page title into a URL
            url = f"https://en.wikipedia.org/wiki/{page.replace(' ', '_')}"
            # Write the URL to the file
            file.write(url + "\n")

if __name__ == "__main__":
    template_name = "Infobox political division"
    parameter_name = "flag_link"
    
    # Get all pages using the template
    pages = get_pages_using_template(template_name)
    
    # Filter pages that don't use the specified parameter
    filtered_pages = filter_pages_without_parameter(pages, parameter_name)
    
    # Write the filtered list of pages to a text file
    write_links_to_file(filtered_pages)
