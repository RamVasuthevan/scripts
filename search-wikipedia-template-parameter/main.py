import requests
import re

def get_pages_using_template(template_name, limit=500):
    """
    Retrieves a list of pages that embed the specified template.

    Args:
    - template_name: The name of the template to search for.
    - limit: The maximum number of results per request.

    Returns:
    - A list of page titles using the specified template.
    """
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

        pages.extend([item['title'] for item in data['query']['embeddedin']])

        if "continue" in data:
            params.update(data["continue"])
        else:
            break

    return pages

def fetch_page_content(page_title):
    """
    Fetches the raw content of a Wikipedia page.

    Args:
    - page_title: The title of the Wikipedia page.

    Returns:
    - The raw content of the page.
    """
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": page_title,
        "rvprop": "content",
        "rvslots": "main",
    }

    response = requests.get(url, params=params)
    data = response.json()
    
    page_id = next(iter(data['query']['pages']))
    content = data['query']['pages'][page_id]['revisions'][0]['slots']['main']['*']
    
    return content

def filter_pages_by_parameter(pages, parameter):
    """
    Filters pages that contain the specified template parameter with a non-empty value.

    Args:
    - pages: A list of page titles to check.
    - parameter: The template parameter to search for.

    Returns:
    - A list of page titles that use the specified parameter with a non-empty value.
    """
    filtered_pages = []
    
    # Regex to find non-empty parameter values
    parameter_regex = re.compile(
        r'{{Infobox political division[^}]*\|\s*' + re.escape(parameter) + r'\s*=\s*([^|\n}]+)', 
        re.IGNORECASE
    )

    for page in pages:
        content = fetch_page_content(page)
        match = parameter_regex.search(content)
        
        # Check if the parameter exists and has a non-empty value
        if match and match.group(1).strip():
            filtered_pages.append(page)

    return filtered_pages

def write_links_to_file(pages, filename="results.txt"):
    """
    Writes the Wikipedia page URLs to a text file.

    Args:
    - pages: A list of page titles.
    - filename: The name of the output text file.
    """
    with open(filename, "w", encoding="utf-8") as file:
        for page in pages:
            url = f"https://en.wikipedia.org/wiki/{page.replace(' ', '_')}"
            file.write(url + "\n")

if __name__ == "__main__":
    template_name = "Infobox political division"
    parameter_to_filter = "flag_link"

    # Get all pages using the specified template
    pages = get_pages_using_template(template_name)

    # Filter pages by the specified parameter
    filtered_pages = filter_pages_by_parameter(pages, parameter_to_filter)

    # Write filtered pages to a text file
    write_links_to_file(filtered_pages)
