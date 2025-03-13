#!/usr/bin/env python3

import requests
import getpass
import csv
import os
import xml.etree.ElementTree as ET
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 about not verifying the SSL cert
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def get_api_key(fw_ip, username, password):
    """
    Retrieve an API key from the firewall using the 'keygen' call.
    Returns the key as a string, or None if unsuccessful.
    """
    url = f"https://{fw_ip}/api/"
    params = {
        "type": "keygen",
        "user": username,
        "password": password
    }
    try:
        r = requests.get(url, params=params, verify=False, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        # The key is typically found at response/result/key
        key_element = root.find("./result/key")
        if key_element is not None:
            return key_element.text.strip()
        else:
            return None
    except Exception as e:
        print(f"[ERROR] Could not retrieve API key from {fw_ip}: {e}")
        return None

def get_system_info(fw_ip, api_key):
    """
    Use the XML API to run 'show system info'.
    Returns (hostname, serial_number) as a tuple.
    """
    url = f"https://{fw_ip}/api/"
    cmd = "<show><system><info></info></system></show>"
    params = {
        "type": "op",
        "cmd": cmd,
        "key": api_key
    }
    try:
        r = requests.get(url, params=params, verify=False, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)

        hostname = root.find(".//hostname")
        serial = root.find(".//serial")

        hostname_str = hostname.text.strip() if hostname is not None else "N/A"
        serial_str = serial.text.strip() if serial is not None else "N/A"

        return hostname_str, serial_str
    except Exception as e:
        print(f"[ERROR] Failed to retrieve system info from {fw_ip}: {e}")
        return ("N/A", "N/A")

def get_loopback109_ip(fw_ip, api_key):
    """
    Use the XML API to run 'show interface loopback.109'.
    Returns the IP address as a string (including mask, e.g. 10.1.109.1/24),
    or "N/A" if not found.
    """
    url = f"https://{fw_ip}/api/"
    cmd = "<show><interface>loopback.109</interface></show>"
    params = {
        "type": "op",
        "cmd": cmd,
        "key": api_key
    }
    try:
        r = requests.get(url, params=params, verify=False, timeout=10)
        r.raise_for_status()
        root = ET.fromstring(r.text)
        # Typical relevant path might be something like .//result/hw/ip
        ip_elem = root.find(".//ip")
        if ip_elem is not None and ip_elem.text:
            return ip_elem.text.strip()
        else:
            return "N/A"
    except Exception as e:
        print(f"[ERROR] Failed to retrieve loopback.109 IP from {fw_ip}: {e}")
        return "N/A"

def main():
    # Prompt for credentials
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    # Prompt for the file containing the list of firewall IP addresses
    device_file = input("Enter path to file containing firewall IPs: ")
    if not os.path.isfile(device_file):
        print(f"[ERROR] File {device_file} does not exist.")
        return

    # Read firewall IPs from file
    with open(device_file, 'r') as f:
        firewall_ips = [line.strip() for line in f if line.strip()]

    output_csv = "pa_devices.csv"
    # Prepare CSV for writing
    with open(output_csv, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Hostname", "Serial Number", "Loopback.109 IP", "Firewall MGMT IP"])

        for fw_ip in firewall_ips:
            print(f"\n[INFO] Processing device {fw_ip} ...")

            # 1) Retrieve API Key
            api_key = get_api_key(fw_ip, username, password)
            if not api_key:
                print(f"[ERROR] Could not retrieve API key for {fw_ip}. Skipping.")
                writer.writerow(["N/A", "N/A", "N/A", fw_ip])
                continue

            # 2) Get system info (hostname, serial)
            hostname, serial = get_system_info(fw_ip, api_key)

            # 3) Get loopback.109 IP
            loop109_ip = get_loopback109_ip(fw_ip, api_key)

            # Write row to CSV
            writer.writerow([hostname, serial, loop109_ip, fw_ip])

            print(f"[SUCCESS] {fw_ip}: Hostname={hostname}, Serial={serial}, Loopback.109={loop109_ip}")

    print(f"\n[DONE] Results have been saved to {output_csv}.")

if __name__ == "__main__":
    main()
