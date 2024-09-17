import xml.etree.ElementTree as ET
import sqlite3
import logging
import os
from datetime import datetime
from typing import Optional

# Configure logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(filename)s (%(lineno)d) - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Set console output to WARNING and above
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
logging.getLogger().addHandler(console_handler)

# Define the namespace
NS = {'cc': 'http://www.ic.gc.ca/corpcan'}
DB_NAME = 'canadian_corps.db' + datetime.now().strftime('%Y%m%d_%H%M%S')

def create_database() -> sqlite3.Connection:
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE corporations (
            corporation_id INTEGER PRIMARY KEY, 
            business_number TEXT
        );
        
        CREATE TABLE names (
            corporation_id INTEGER,
            name TEXT,
            code TEXT,
            current BOOLEAN,
            effective_date TEXT,
            expiry_date TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );
        
        CREATE TABLE addresses (
            corporation_id INTEGER,
            code TEXT,
            address_line1 TEXT,
            address_line2 TEXT,
            city TEXT,
            province TEXT,
            country TEXT,
            postal_code TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );
        
        CREATE TABLE activities (
            corporation_id INTEGER,
            code TEXT,
            date TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );

        CREATE TABLE annual_returns (
            corporation_id INTEGER,
            annual_meeting_date TEXT,
            type_of_corporation_code TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );

        CREATE TABLE acts (
            corporation_id INTEGER,
            code TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );

        CREATE TABLE statuses (
            corporation_id INTEGER,
            code TEXT,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );

        CREATE TABLE director_limits (
            corporation_id INTEGER,
            minimum INTEGER,
            maximum INTEGER,
            FOREIGN KEY (corporation_id) REFERENCES corporations(corporation_id)
        );
    ''')

    conn.commit()
    return conn

def parse_xml_file(file_path: str, conn: sqlite3.Connection) -> None:
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise RuntimeError(f"Error parsing {file_path}: {e}")

    c = conn.cursor()

    for corporation in root.findall('.//corporation', NS):
        corp_id = corporation.get('corporationId')
        if corp_id is None:
            raise ValueError(f"Corporation without ID found in {file_path}")

        try:
            process_corporation(c, corp_id, corporation, file_path)
        except Exception as e:
            logging.error(f"Error processing corporation {corp_id} in {file_path}: {e}")
            raise

    conn.commit()

def process_corporation(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    business_number = get_business_number(corporation)
    
    c.execute("INSERT INTO corporations (corporation_id, business_number) VALUES (?, ?)",
              (corp_id, business_number))

    process_names(c, corp_id, corporation, file_path)
    process_addresses(c, corp_id, corporation, file_path)
    process_activities(c, corp_id, corporation, file_path)
    process_annual_returns(c, corp_id, corporation, file_path)
    process_acts(c, corp_id, corporation, file_path)
    process_statuses(c, corp_id, corporation, file_path)
    process_director_limits(c, corp_id, corporation, file_path)

def get_business_number(corporation: ET.Element) -> Optional[str]:
    business_numbers = corporation.find('.//businessNumbers', NS)
    if business_numbers is not None:
        business_number = business_numbers.find('businessNumber', NS)
        if business_number is not None:
            return business_number.text
    return None

def process_names(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    names = corporation.findall('.//name', NS)
    if not names:
        logging.warning(f"Corporation {corp_id} has no names in file {file_path}")
        return
    for name in names:
        c.execute("INSERT INTO names VALUES (?, ?, ?, ?, ?, ?)",
                  (corp_id, name.text, name.get('code'), name.get('current') == 'true',
                   name.get('effectiveDate'), name.get('expiryDate')))

def process_addresses(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    addresses = corporation.findall('.//address', NS)
    if not addresses:
        logging.warning(f"Corporation {corp_id} has no addresses in file {file_path}")
        return
    for address in addresses:
        address_lines = address.findall('addressLine', NS)
        address_line1 = address_lines[0].text if address_lines else None
        address_line2 = address_lines[1].text if len(address_lines) > 1 else None
        
        city = address.find('city', NS)
        province = address.find('province', NS)
        country = address.find('country', NS)
        postal_code = address.find('postalCode', NS)

        c.execute("INSERT INTO addresses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (corp_id, address.get('code'),
                   address_line1,
                   address_line2,
                   city.text if city is not None else None,
                   province.get('code') if province is not None else None,
                   country.get('code') if country is not None else None,
                   postal_code.text if postal_code is not None else None))

def process_activities(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    activities = corporation.findall('.//activity', NS)
    if not activities:
        logging.warning(f"Corporation {corp_id} has no activities in file {file_path}")
        return
    for activity in activities:
        c.execute("INSERT INTO activities VALUES (?, ?, ?)",
                  (corp_id, activity.get('code'), activity.get('date')))

def process_annual_returns(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    annual_returns = corporation.find('.//annualReturns', NS)
    if annual_returns is None:
        return
    for annual_return in annual_returns.findall('annualReturn', NS):
        annual_meeting_date = annual_return.find('annualMeetingDate', NS)
        type_of_corporation = annual_return.find('typeOfCorporation', NS)
        c.execute("INSERT INTO annual_returns VALUES (?, ?, ?)",
                  (corp_id, 
                   annual_meeting_date.text if annual_meeting_date is not None else None,
                   type_of_corporation.get('code') if type_of_corporation is not None else None))

def process_acts(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    acts = corporation.find('.//acts', NS)
    if acts is None:
        return
    for act in acts.findall('act', NS):
        c.execute("INSERT INTO acts VALUES (?, ?)",
                  (corp_id, act.get('code')))

def process_statuses(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    statuses = corporation.find('.//statuses', NS)
    if statuses is None:
        return
    for status in statuses.findall('status', NS):
        c.execute("INSERT INTO statuses VALUES (?, ?)",
                  (corp_id, status.get('code')))

def process_director_limits(c: sqlite3.Cursor, corp_id: str, corporation: ET.Element, file_path: str) -> None:
    director_limits = corporation.find('.//directorLimits', NS)
    if director_limits is None:
        return
    for director_limit in director_limits.findall('directorLimit', NS):
        minimum = director_limit.find('minimum', NS)
        maximum = director_limit.find('maximum', NS)
        c.execute("INSERT INTO director_limits VALUES (?, ?, ?)",
                  (corp_id, 
                   int(minimum.text) if minimum is not None else None,
                   int(maximum.text) if maximum is not None else None))

def process_all_files(directory: str) -> None:
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory {directory} does not exist.")

    conn = create_database()

    # Get all XML files and sort them
    xml_files = [f for f in os.listdir(directory) if f.startswith("OPEN_DATA_") and f.endswith(".xml")]
    xml_files.sort(key=lambda x: int(x.split('_')[2].split('.')[0]))

    for filename in xml_files:
        file_path = os.path.join(directory, filename)
        logging.info(f"Processing {filename}...")
        try:
            parse_xml_file(file_path, conn)
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            raise

    conn.close()

def log_final_stats() -> None:
    logging.info("Starting final statistics logging...")
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    tables = ['corporations', 'names', 'addresses', 'activities', 
              'annual_returns', 'acts', 'statuses', 'director_limits']
    
    for table in tables:
        logging.info(f"Counting {table}...")
        count = c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        logging.info(f"Total {table}: {count}")

    logging.info("Counting corporations without business numbers...")
    c.execute("SELECT COUNT(*) FROM corporations WHERE business_number IS NULL")
    corps_without_bn = c.fetchone()[0]
    logging.info(f"Corporations without business numbers: {corps_without_bn}")

    logging.info("Counting corporations without names...")
    c.execute("""
        SELECT 
            (SELECT COUNT(DISTINCT corporation_id) FROM corporations) -
            (SELECT COUNT(DISTINCT corporation_id) FROM names)
    """)
    corps_without_names = c.fetchone()[0]
    logging.info(f"Corporations without names: {corps_without_names}")

    logging.info("Closing database connection...")
    conn.close()
    logging.info("Processing complete.")

if __name__ == "__main__":
    xml_directory = "OPEN_DATA_SPLIT"
    process_all_files(xml_directory)
    log_final_stats()