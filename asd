import sys
import csv
import xml.etree.ElementTree as ET
import requests
from getpass import getpass

# Disable SSL certificate warnings
requests.packages.urllib3.disable_warnings()

def check_panorama_certs():
    # Read input IPs
    print("Enter Panorama IP addresses (one per line), followed by 'end' on a new line:")
    ip_list = []
    for line in sys.stdin:
        line = line.strip()
        if line.lower() == 'end':
            break
        if line:
            ip_list.append(line)

    if not ip_list:
        print("No IP addresses provided.", file=sys.stderr)
        return

    # Get credentials
    username = input("Enter Panorama username: ")
    password = getpass("Enter Panorama password: ")

    results = []

    for ip in ip_list:
        hostname = "unknown"
        cert_present = False
        cert_name = ""
        api_key = None

        # Get API key
        try:
            keygen_url = f"https://{ip}/api/?type=keygen&user={username}&password={password}"
            response = requests.get(keygen_url, verify=False, timeout=10)
            root = ET.fromstring(response.content)
            if root.attrib.get('status') == 'success':
                api_key = root.find('.//key').text
            else:
                results.append([hostname, ip, cert_present, cert_name])
                continue
        except Exception as e:
            print(f"Error connecting to {ip}: {str(e)}", file=sys.stderr)
            results.append([hostname, ip, cert_present, cert_name])
            continue

        # Get hostname
        try:
            sysinfo_url = f"https://{ip}/api/?type=op&cmd=<show><system><info></info></system></show>&key={api_key}"
            response = requests.get(sysinfo_url, verify=False, timeout=10)
            sys_root = ET.fromstring(response.content)
            hostname = sys_root.find('.//hostname').text.strip()
        except:
            hostname = "unknown"

        # Check SSL/TLS profile
        try:
            ssl_url = f"https://{ip}/api/?type=config&action=get&xpath=/config/panorama/ssl-tls-service-profile&key={api_key}"
            response = requests.get(ssl_url, verify=False, timeout=10)
            ssl_root = ET.fromstring(response.content)
            
            entry = ssl_root.find('.//ssl-tls-service-profile/entry')
            if entry is not None:
                cert_present = True
                cert_name = entry.attrib.get('name', '')
        except Exception as e:
            print(f"Error checking SSL profile on {ip}: {str(e)}", file=sys.stderr)

        results.append([hostname, ip, cert_present, cert_name])

    # Output CSV
    writer = csv.writer(sys.stdout)
    writer.writerow(['Hostname', 'IP Address', 'Certificate Present', 'Certificate Name'])
    writer.writerows(results)

if __name__ == "__main__":
    check_panorama_certs()
