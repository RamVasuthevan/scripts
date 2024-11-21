import re
from collections import namedtuple
import whois

DNSRecord = namedtuple('DNSRecord', ['name', 'ttl', 'record_class', 'record_type', 'rdata'])

def parse_zone_file(file_path):
    records = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith(';'):  # Skip empty lines and comments
                parts = re.split(r'\s+', line)
                if len(parts) >= 5:
                    name = parts[0]
                    ttl = parts[1]
                    record_class = parts[2]
                    record_type = parts[3]
                    rdata = ' '.join(parts[4:])
                    record = DNSRecord(name, ttl, record_class, record_type, rdata)
                    records.append(record)
    return records

def is_domain_registered(domain):
    try:
        w = whois.whois(domain)
        return bool(w.domain_name)
    except whois.parser.PywhoisError:
        return False
    except Exception as e:
        print(f"Error checking {domain}: {str(e)}")
        return False

# Example usage
zone_file_path = 'data/toys.txt'
parsed_records = parse_zone_file(zone_file_path)

data = set()
for record in parsed_records:
    data.add(record.name[:-1])  # Remove the trailing dot
    #print(f"Name: {record.name}, Type: {record.record_type}, Data: {record.rdata}")

print(f"Total unique domains: {len(data)}")

for name in sorted(data):
    com_domain = f"{name.split('.')[0]}toys.com"
    registration_status = "registered" if is_domain_registered(com_domain) else "not registered"
    
    print(f"{com_domain} is {registration_status}")