import imaplib
import email
from email.message import Message
from dotenv import load_dotenv
import os
from typing import List, Optional, Tuple, Union
from bs4 import BeautifulSoup
import logging
import requests
from urllib.parse import urlparse, unquote
import zipfile
import json
from datetime import datetime
from git import Repo, InvalidGitRepositoryError
import shutil

# Magic variables
SAVE_DIR: str = "dogsheep-data/myfitnesspal-export"
FROM_ADDRESS: str = "no-reply@myfitnesspal.com"
SUBJECT: str = "Your MyFitnessPal Export"
IMAP_PORT: int = 993
LOG_FILE: str = "email_processing.log"
DOGSHEEP_REPO_URL: str = "https://github.com/RamVasuthevan/dogsheep-data.git"

# Configure logging to write only to a file
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE)],
)

logger = logging.getLogger(__name__)


def connect_to_email() -> imaplib.IMAP4_SSL:
    """Connect to the email server and log in."""
    load_dotenv()
    validate_environment_variables()

    email_user: str = os.getenv("EMAIL_USER")
    email_password: str = os.getenv("EMAIL_PASSWORD")
    imap_url: str = os.getenv("IMAP_URL")

    logger.info("Connecting to the email server")
    mail = imaplib.IMAP4_SSL(imap_url, IMAP_PORT)
    mail.login(email_user, email_password)
    logger.info("Connected and logged in to the email server")
    return mail


def search_and_fetch_emails(
    mail: imaplib.IMAP4_SSL, from_address: str, subject: str
) -> List[Message]:
    """Search for emails from a specific sender with a specific subject and return them."""

    logger.info(
        f"Searching and fetching emails from '{from_address}' with subject '{subject}'"
    )
    mail.select("inbox", readonly=True)
    search_criteria: str = f'(FROM "{from_address}" SUBJECT "{subject}")'
    charset = None
    status: str
    email_ids_data: List[bytes]
    status, email_ids_data = mail.search(charset, search_criteria)

    email_ids: List[bytes] = email_ids_data[0].split()
    logger.info(f"Search completed. Number of emails found: {len(email_ids)}")

    emails = []
    for mail_id in email_ids:
        status: str
        msg_data: List[Tuple[bytes, bytes]]
        status, msg_data = mail.fetch(mail_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg_bytes = response_part[1]
                msg = email.message_from_bytes(msg_bytes)
                emails.append(msg)

    return emails


def process_multipart_email(msg: Message) -> Optional[str]:
    """Process a multipart email and extract the download link."""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html_content: str = part.get_payload(decode=True).decode()
            return extract_and_return_link(html_content)
    return None


def process_singlepart_email(msg: Message) -> Optional[str]:
    """Process a single-part email and extract the download link."""
    if msg.get_content_type() == "text/html":
        html_content: str = msg.get_payload(decode=True).decode()
        return extract_and_return_link(html_content)
    return None


def extract_and_return_link(html_content: str) -> Optional[str]:
    """Extract and return the download link from the HTML content."""
    soup = BeautifulSoup(html_content, "lxml")
    body_div = soup.find("div", class_="mfp-default--body")
    if body_div:
        download_link = body_div.find("a", string="Download Files")
        if download_link:
            return download_link["href"]
    return None


def get_filename_from_content_disposition(headers) -> Optional[str]:
    """Extract the filename from the Content-Disposition header."""
    content_disposition = headers.get("Content-Disposition")
    if content_disposition:
        parts = content_disposition.split(";")
        for part in parts:
            if "filename=" in part:
                filename = part.split("=")[1].strip('"')
                return filename
    return None


def get_filename_from_url(url: str) -> str:
    """Extract the filename from the URL."""
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return unquote(filename)  # Decodes URL-encoded characters


def download_file(url: str, save_dir: str) -> Optional[str]:
    """Download a file from the given URL and return the path where it was saved."""
    logger.info(f"Starting download from {url}")
    response = requests.get(url, stream=True)

    if response.status_code == 403 and "Request has expired" in response.text:
        logger.info(f"Download link has expired: {url}")
        return None

    if response.status_code == 200:
        # Attempt to get the filename from the Content-Disposition header
        filename: Optional[str] = get_filename_from_content_disposition(
            response.headers
        )
        if not filename:
            # Fallback to extracting the filename from the URL if Content-Disposition is not available
            filename = get_filename_from_url(url)

        # Ensure the save directory exists
        os.makedirs(save_dir, exist_ok=True)

        # Save the file to the specified directory
        save_path: str = os.path.join(save_dir, filename)
        logger.info(f"Saving file as {save_path}")

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        logger.info(f"File downloaded and saved as {save_path}")

        return save_path
    else:
        logger.error(
            f"Failed to download file from {url}. Status code: {response.status_code}"
        )
        return None


def get_script_info() -> dict:
    """
    Retrieve information about the script's Git repository, including the commit hash,
    repository URL, and whether there are any uncommitted changes.
    """
    try:
        repo = Repo(os.path.dirname(__file__), search_parent_directories=True)

        # Get the current commit hash
        commit_hash = repo.head.commit.hexsha

        # Check if there are uncommitted changes
        uncommitted_changes = repo.is_dirty(untracked_files=True)

        # Get the remote origin URL (i.e., the repository URL)
        repo_url = next(repo.remote().urls)

        return {
            "repository": repo_url,
            "commit_hash": commit_hash,
            "uncommitted_changes": uncommitted_changes,
        }
    except InvalidGitRepositoryError:
        logger.error("Not a valid Git repository.")
        return {
            "repository": None,
            "commit_hash": None,
            "uncommitted_changes": None,
        }


def clone_dogsheep_data(branch: str) -> str:
    """Clone the dogsheep-data repository to a temporary directory."""
    repo_dir = "dogsheep-data"
    if os.path.exists(repo_dir):
        shutil.rmtree(repo_dir)
    logger.info(f"Cloning dogsheep-data repository from branch '{branch}'")
    Repo.clone_from(DOGSHEEP_REPO_URL, repo_dir, branch=branch)
    return repo_dir


def write_extracted_files(
    zip_path: str, extract_dir: str, message_id: str, email_message: Message
):
    """Extract the ZIP file, write metadata about the email, and delete the ZIP file."""
    # Ensure the extract directory exists
    os.makedirs(extract_dir, exist_ok=True)

    # Extract the contents of the ZIP file
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
        logger.info(f"Extracted contents of {zip_path} to {extract_dir}")

    # Write metadata about the email
    git_info = get_script_info()
    metadata = {
        "message_id": message_id,
        "subject": email_message.get("Subject"),
        "from": email_message.get("From"),
        "date": email_message.get("Date"),
        "to": email_message.get("To"),
        "extracted_on": datetime.now().isoformat(),
        "git_repository": git_info.get("repository"),
        "git_commit_hash": git_info.get("commit_hash"),
        "uncommitted_changes": git_info.get("uncommitted_changes"),
    }
    metadata_path = os.path.join(extract_dir, "metadata.json")
    with open(metadata_path, "w") as metadata_file:
        json.dump(metadata, metadata_file, indent=4)
    logger.info(f"Wrote metadata to {metadata_path}")

    # Delete the ZIP file
    os.remove(zip_path)
    logger.info(f"Deleted the ZIP file: {zip_path}")


def extract_date_range_from_filename(zip_path: str) -> str:
    """Extract the date range from the ZIP filename."""
    filename = os.path.basename(zip_path)
    date_range = filename.split("File-Export-")[-1].split(".zip")[0]
    return date_range


def commit_untracked_files_to_repo(repo_dir: str, script_name: str):
    """Commit only untracked files in the dogsheep-data repository."""
    try:
        repo = Repo(repo_dir)

        # Get a list of all untracked files in the extract_dir
        untracked_files = repo.untracked_files
        print(f"Untracked files:")
        for file in untracked_files:
            print("\t", file)

        if untracked_files:
            # Stage only untracked files
            repo.index.add(untracked_files)
            logger.info(f"Staged untracked files: {untracked_files}")

            git_info = get_script_info()
            commit_message = (
                f"MyFitnessPal Export\n"
                f"Script: {script_name}\n"
                f"Repository: {git_info['repository']}\n"
                f"Commit hash: {git_info['commit_hash']}\n"
                f"Uncommitted changes: {git_info['uncommitted_changes']}"
            )

            # Commit the changes
            repo.index.commit(commit_message)
            # Push the changes
            origin = repo.remote(name="origin")
            origin.push()
            logger.info(f"Committed and pushed untracked files for MyFitnessPal Export")
        else:
            logger.info("No untracked files detected; skipping commit.")
    except InvalidGitRepositoryError:
        logger.error("Not a valid Git repository. Cannot commit changes.")
    except Exception as e:
        logger.error(f"Failed to commit untracked files: {e}")


def format_date_for_folder(date_str: str) -> str:
    """Format the email date string for use in a folder name."""
    date_obj = email.utils.parsedate_to_datetime(date_str)
    return date_obj.strftime("%Y%m%d_%H%M%S")


def process_emails(emails: List[Message]):
    """Process all relevant emails."""
    for email_message in emails:
        message_id: str = email_message.get("Message-ID")
        logger.info(f"Processing email with Message-ID: {message_id}")

        # Extract the download link
        link = None
        if email_message.is_multipart():
            logger.info(f"{message_id}: Processing multipart email")
            link = process_multipart_email(email_message)
        else:
            logger.info(f"{message_id}: Processing singlepart email")
            link = process_singlepart_email(email_message)

        if link:
            logger.info(f"{message_id}: Download link: {link}")
            # Format the date for the folder name
            formatted_date = format_date_for_folder(email_message.get("Date"))
            # Download the file
            zip_path = download_file(link, save_dir=SAVE_DIR)
            if zip_path:
                # Set the extraction directory and write metadata
                extract_dir = os.path.join(
                    SAVE_DIR,
                    f"{formatted_date}_{os.path.splitext(os.path.basename(zip_path))[0]}_{message_id}",
                )
                write_extracted_files(zip_path, extract_dir, message_id, email_message)
            else:
                logger.warning(
                    f"{message_id}: Skipping processing due to expired download link."
                )
        else:
            logger.warning(f"{message_id}: No download link found in the email.")


def validate_environment_variables():
    """Validate that all required environment variables are set."""
    required_vars = ["EMAIL_USER", "EMAIL_PASSWORD", "IMAP_URL"]
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set")


def main():
    logger.info("Starting the email processing script")

    branch = "main"

    try:
        # Clone the dogsheep-data repository
        repo_dir: str = clone_dogsheep_data(branch)

        # Connect to email
        mail: imaplib.IMAP4_SSL = connect_to_email()
        emails: List[Message] = search_and_fetch_emails(mail, FROM_ADDRESS, SUBJECT)
        # Process the emails
        process_emails(emails)

        # Commit untracked files to the repository
        commit_untracked_files_to_repo(repo_dir, os.path.basename(__file__))

    finally:
        logger.info("Logging out from the email server")
        mail.logout()


if __name__ == "__main__":
    main()
