import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

def connect_to_email():
    """Connect to the email server and log in."""
    load_dotenv()

    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    imap_url = os.getenv('IMAP_URL')

    mail = imaplib.IMAP4_SSL(imap_url, 993)
    mail.login(email_user, email_password)
    return mail

def search_emails(mail):
    """Search for emails with specific subject and sender."""
    mail.select('inbox', readonly=True)
    status, messages = mail.search(
        None,
        '(FROM "no-reply@myfitnesspal.com" SUBJECT "Your MyFitnessPal Export")'
    )
    return messages[0].split()

def fetch_and_process_email(mail, mail_id):
    """Fetch an email by ID and process it."""
    status, msg_data = mail.fetch(mail_id, '(RFC822)')

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            print_metadata(msg)

            if msg.is_multipart():
                print("****TRUE*****")
                process_multipart_email(msg)
            else:
                print("****FALSE*****")
                process_singlepart_email(msg)

def print_metadata(msg):
    """Print the metadata of the email."""
    print("----- Email Metadata -----")
    print(f"Date: {msg.get('Date')}")
    print(f"Message-ID: {msg.get('Message-ID')}")
    print("----------------------------")

def process_multipart_email(msg):
    """Process a multipart email."""
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html_content = part.get_payload(decode=True).decode()
            extract_and_print_link(html_content)

def process_singlepart_email(msg):
    """Process a single-part email."""
    if msg.get_content_type() == 'text/html':
        html_content = msg.get_payload(decode=True).decode()
        extract_and_print_link(html_content)

def extract_and_print_link(html_content):
    """Extract and print the download link from the email's HTML content."""
    soup = BeautifulSoup(html_content, 'lxml')
    body_div = soup.find('div', class_='mfp-default--body')
    if body_div:
        download_link = body_div.find('a', string='Download Files')
        if download_link:
            print(f"Download Link Text: {download_link.text}")
            print(f"Download Link URL: {download_link['href']}")

def main():
    """Main function to run the email processing."""
    mail = connect_to_email()
    try:
        messages = search_emails(mail)
        for mail_id in messages:
            fetch_and_process_email(mail, mail_id)
    finally:
        mail.logout()

if __name__ == "__main__":
    main()
