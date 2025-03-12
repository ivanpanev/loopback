import requests
import json
import concurrent.futures
from getpass import getpass
import xml.etree.ElementTree as ET

requests.packages.urllib3.disable_warnings()

MAX_WORKERS = 10

def get_api_key(ip, username, password):
    """Obtain an API key via the XML API keygen call."""
    url = f"https://{ip}/api/?type=keygen&user={username}&password={password}"
    try:
        resp = requests.get(url, verify=False, timeout=10)
        if resp.status_code == 200 and "<key>" in resp.text:
            return resp.text.split("<key>")[1].split("</key>")[0]
    except Exception as e:
        print(f"[{ip}] Exception in get_api_key: {e}")
    return None

def get_os_version(ip, api_key):
    """Use the XML API to retrieve the device's major.minor version (e.g., 10.1 or 10.2)."""
    url = f"https://{ip}/api/?type=op&cmd=<show><system><info></info></system></show>"
    headers = {"X-PAN-KEY": api_key}
    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.text)
            full_version = root.find(".//sw-version").text  # e.g. "10.2.3-h4"
            version_parts = full_version.split(".")
            return ".".join(version_parts[:2])  # e.g. "10.2"
    except Exception as e:
        print(f"[{ip}] Exception in get_os_version: {e}")
    # Fallback if we can't parse anything:
    return "10.2"

def get_loopback109_ip_addresses(ip, api_key, os_version):
    """
    Retrieves the IP(s) configured on loopback.109 (if any).
    Returns a list of IP strings in CIDR form, or an empty list if none/not found.
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name=loopback.109"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    try:
        resp = requests.get(url, headers=headers, verify=False, timeout=10)
        if resp.status_code != 200:
            return []  # Not found or error

        data = resp.json()
        # We expect data["result"]["entry"] to contain the interface definition
        entry = data["result"].get("entry")
        if isinstance(entry, list):
            entry = entry[0] if entry else {}

        if not entry:
            return []

        # The IP addresses are in entry["ip"]["entry"], if present
        ip_block = entry.get("ip", {}).get("entry", [])
        if isinstance(ip_block, dict):
            # If the firewall returns a single dict instead of a list
            ip_block = [ip_block]

        # Each item has "@name" = "<IP>/CIDR"
        addresses = [item.get("@name") for item in ip_block if "@name" in item]
        return addresses
    except Exception as e:
        print(f"[{ip}] Exception in get_loopback109_ip_addresses: {e}")
        return []

def fetch_device_loopback(ip, username, password):
    """
    Main worker function: logs in, retrieves loopback.109 addresses, returns a list of them.
    """
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return (ip, None, "Failed to obtain API key")

    os_ver = get_os_version(ip, api_key)
    loop_ips = get_loopback109_ip_addresses(ip, api_key, os_ver)
    if not loop_ips:
        return (ip, [], "No IP found or loopback.109 missing.")
    return (ip, loop_ips, "OK")

def main():
    username = input("Enter username: ").strip()
    password = getpass("Enter password: ").strip()

    print("Enter firewall IP addresses (one per line). Type 'end' to finish:")
    devices = []
    while True:
        line = input().strip()
        if line.lower() == "end":
            break
        if line:
            devices.append(line)

    print("\nWorking...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        for dev in devices:
            f = executor.submit(fetch_device_loopback, dev, username, password)
            future_map[f] = dev

        for fut in concurrent.futures.as_completed(future_map):
            ip, loop_ips, msg = fut.result()
            results.append((ip, loop_ips, msg))

    print("\n=== Loopback.109 Addresses ===")
    for ip, ip_list, msg in results:
        if ip_list is None:
            # Means we couldn't even get an API key
            print(f"{ip} -> ERROR: {msg}")
        elif len(ip_list) == 0:
            # Means no IP found or missing loopback
            print(f"{ip} -> {msg}")
        else:
            print(f"{ip} -> {', '.join(ip_list)}")

if __name__ == "__main__":
    main()
