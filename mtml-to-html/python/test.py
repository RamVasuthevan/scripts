from bs4 import BeautifulSoup
import email

# Replace this with the path to your MHTML file
mhtml_file_path = "I Can Tolerate Anything Except The Outgroup _ Slate Star Codex.mhtml"
output_html_file_path = "output.html"

# Load and parse the MHTML file
with open(mhtml_file_path, "r", encoding="utf-8") as file:
    msg = email.message_from_file(file)

    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_content = part.get_payload(decode=True)
            soup = BeautifulSoup(html_content, "html.parser")

            # Save the HTML content
            with open(output_html_file_path, "w", encoding="utf-8") as output_file:
                output_file.write(soup.prettify())

print(f"Conversion complete! HTML file saved as {output_html_file_path}")
