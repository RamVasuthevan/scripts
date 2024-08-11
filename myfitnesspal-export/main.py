import imaplib
import email
from email.message import Message
from dotenv import load_dotenv
import os
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup
import logging

# Configure logging to write only to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("email_processing.log")
    ]
)

logger = logging.getLogger(__name__)

def connect_to_email() -> imaplib.IMAP4_SSL:
    """Connect to the email server and log in."""
    load_dotenv()

    email_user: str = os.getenv('EMAIL_USER')
    email_password: str = os.getenv('EMAIL_PASSWORD')
    imap_url: str = os.getenv('IMAP_URL')

    logger.info("Connecting to the email server")
    mail = imaplib.IMAP4_SSL(imap_url, 993)
    mail.login(email_user, email_password)
    logger.info("Connected and logged in to the email server")
    return mail

def search_emails(mail: imaplib.IMAP4_SSL) -> List[bytes]:
    """Search for emails with specific subject and sender."""
    logger.info("Selecting the inbox for searching")
    mail.select('inbox', readonly=True)
    status, messages = mail.search(
        None,
        '(FROM "no-reply@myfitnesspal.com" SUBJECT "Your MyFitnessPal Export")'
    )
    logger.info(f"Search completed. Number of emails found: {len(messages[0].split())}")
    return messages[0].split()

def fetch_and_process_email(mail: imaplib.IMAP4_SSL, mail_id: bytes) -> Optional[Tuple[str, str]]:
    """Fetch an email by ID and process it."""
    logger.info(f"Fetching email with ID: {mail_id.decode()}")
    status, msg_data = mail.fetch(mail_id, '(RFC822)')

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            message_id = msg.get('Message-ID')
            date = msg.get('Date')

            if msg.is_multipart():
                logger.info(f"{message_id} - {date}: Processing multipart email")
                return process_multipart_email(msg)
            else:
                logger.info(f"{message_id} - {date}: Processing singlepart email")
                return process_singlepart_email(msg)

    return None

def process_multipart_email(msg: Message) -> Optional[Tuple[str, str]]:
    """Process a multipart email and extract the download link."""
    message_id = msg.get('Message-ID')
    date = msg.get('Date')
    logger.info(f"{message_id} - {date}: Walking through the parts of a multipart email")
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            logger.info(f"{message_id} - {date}: Processing HTML content part")
            html_content = part.get_payload(decode=True).decode()
            return extract_and_return_link(html_content, message_id)

    return None

def process_singlepart_email(msg: Message) -> Optional[Tuple[str, str]]:
    """Process a single-part email and extract the download link."""
    message_id = msg.get('Message-ID')
    date = msg.get('Date')
    logger.info(f"{message_id} - {date}: Processing singlepart email content")
    if msg.get_content_type() == 'text/html':
        html_content = msg.get_payload(decode=True).decode()
        return extract_and_return_link(html_content, message_id)

    return None

def extract_and_return_link(html_content: str, message_id: str) -> Optional[Tuple[str, str]]:
    """Extract and return the download link and the email's Message-ID."""
    logger.info(f"{message_id}: Extracting download link from the HTML content")
    soup = BeautifulSoup(html_content, 'lxml')
    body_div = soup.find('div', class_='mfp-default--body')
    if body_div:
        download_link = body_div.find('a', string='Download Files')
        if download_link:
            logger.info(f"{message_id}: Download link found")
            return message_id, download_link['href']
        else:
            logger.warning(f"{message_id}: Download link not found")
    else:
        logger.warning(f"{message_id}: Body div not found in the HTML content")

    return None

def main():
    """Main function to run the email processing."""
    logger.info("Starting the email processing script")
    mail = connect_to_email()
    try:
        messages = search_emails(mail)
        for mail_id in messages:
            result = fetch_and_process_email(mail, mail_id)
            if result:
                message_id, download_link = result
                logger.info(f"{message_id}: Download link: {download_link}")
    finally:
        logger.info("Logging out from the email server")
        mail.logout()

if __name__ == "__main__":
    main()
