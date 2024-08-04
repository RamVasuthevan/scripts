import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

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

# Select the mailbox you want to check in read-only mode
mail.select('inbox', readonly=True)

# Search for emails with specific subject and sender
status, messages = mail.search(
    None,
    '(FROM "no-reply@myfitnesspal.com" SUBJECT "Your MyFitnessPal Export")'
)

# Convert message IDs to a list
messages = messages[0].split()

# Iterate through each email
for mail_id in messages:
    # Fetch the email by ID
    status, msg_data = mail.fetch(mail_id, '(RFC822)')

    for response_part in msg_data:
        if isinstance(response_part, tuple):
            # Parse the email
            msg = email.message_from_bytes(response_part[1])

            # Decode the email subject
            subject, encoding = decode_header(msg['Subject'])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding if encoding else 'utf-8')

            # Decode the email sender
            sender, encoding = decode_header(msg.get('From'))[0]
            if isinstance(sender, bytes):
                sender = sender.decode(encoding if encoding else 'utf-8')

            # Print the email details
            print(f"Subject: {subject}")
            print(f"From: {sender}")

            # Check if the email is multipart
            if msg.is_multipart():
                # Iterate over each part
                for part in msg.walk():
                    # Check if the part is text or HTML
                    if part.get_content_type() == 'text/plain':
                        # Extract the text content
                        email_content = part.get_payload(decode=True).decode()
                        print(f"Email Content: {email_content}")
            else:
                # If not multipart, get the payload
                email_content = msg.get_payload(decode=True).decode()
                print(f"Email Content: {email_content}")

# Logout from the email server
mail.logout()
