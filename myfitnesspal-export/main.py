import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

# Load environment variables from .env file
load_dotenv()

# Magic variables from the .env file
email_user = os.getenv('EMAIL_USER')
email_password = os.getenv('EMAIL_PASSWORD')
imap_url = os.getenv('IMAP_URL')

# Connect to the email server
mail = imaplib.IMAP4_SSL(imap_url, 993)  # Specify the port 993 for SSL

# Login to your email account
mail.login(email_user, email_password)

# Select the "[Gmail]/All Mail" folder, which contains all emails
mail.select('"[Gmail]/All Mail"', readonly=True)

# Use X-GM-RAW to search across all emails in the account
search_query = 'X-GM-RAW "from:no-reply@myfitnesspal.com subject:\\"Your MyFitnessPal Export\\""'
status, messages = mail.uid('SEARCH', None, search_query)

# Check if any messages were found
if status == "OK" and messages[0]:
    message_uids = messages[0].split()
    print(f"Found {len(message_uids)} messages.")

    # Iterate through each email
    for mail_uid in message_uids:
        # Fetch the email by UID
        status, msg_data = mail.uid('FETCH', mail_uid, '(RFC822)')

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                # Parse the email
                msg = email.message_from_bytes(response_part[1])

                # Check if the email is multipart
                if msg.is_multipart():
                    # Iterate over each part
                    for part in msg.walk():
                        # Check if the part is text/html
                        if part.get_content_type() == 'text/html':
                            # Extract the HTML content
                            html_content = part.get_payload(decode=True).decode()

                            # Parse the HTML with BeautifulSoup
                            soup = BeautifulSoup(html_content, 'lxml')  # Use lxml

                            # Find the .mfp-default--body div and the specific <a> tag
                            body_div = soup.find('div', class_='mfp-default--body')
                            if body_div:
                                # Find the <a> tag with the text "Download Files"
                                download_link = body_div.find('a', string='Download Files')
                                if download_link:
                                    print(f"Download Link Text: {download_link.text}")
                                    print(f"Download Link URL: {download_link['href']}")

                else:
                    # If not multipart, check if it is HTML
                    if msg.get_content_type() == 'text/html':
                        # Extract the HTML content
                        html_content = msg.get_payload(decode=True).decode()

                        # Parse the HTML with BeautifulSoup
                        soup = BeautifulSoup(html_content, 'lxml')  # Use lxml

                        # Find the .mfp-default--body div and the specific <a> tag
                        body_div = soup.find('div', class_='mfp-default--body')
                        if body_div:
                            # Find the <a> tag with the text "Download Files"
                            download_link = body_div.find('a', string='Download Files')
                            if download_link:
                                print(f"Download Link Text: {download_link.text}")
                                print(f"Download Link URL: {download_link['href']}")
else:
    print("No messages found.")

# Logout from the email server
mail.logout()
