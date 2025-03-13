import requests
import xml.etree.ElementTree as ET
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 about not verifying the SSL cert.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_loopback109_ip(fw_ip, api_key):
    """
    Query the firewall for 'show interface loopback.109' via the XML API,
    parse the response, and return the IP address (e.g. 172.30.254.254/32).
    """
    url = f"https://{fw_ip}/api/"
    cmd = "<show><interface>loopback.109</interface></show>"
    params = {
        "type": "op",
        "cmd": cmd,
        "key": api_key
    }
    try:
        # Send request to firewall
        r = requests.get(url, params=params, verify=False, timeout=10)
        r.raise_for_status()

        # Parse XML
        root = ET.fromstring(r.text)

        # Locate the <member> element under <ifnet><addr>
        # which contains the IP address/mask, e.g. "172.30.254.254/32"
        member_elem = root.find(".//ifnet/addr/member")
        if member_elem is None or not member_elem.text:
            return "N/A"

        return member_elem.text.strip()

    except Exception as e:
        print(f"[ERROR] Failed to retrieve loopback.109 IP from {fw_ip}: {e}")
        return "N/A"
