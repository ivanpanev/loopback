import requests
import json
import concurrent.futures
from getpass import getpass
from ipaddress import ip_network, ip_address
import xml.etree.ElementTree as ET

# Disable SSL warnings (not recommended for production)
requests.packages.urllib3.disable_warnings()

# Constants
MAX_WORKERS = 10
API_KEY_ENDPOINT = "/api/?type=keygen&user={}&password={}"
HA_STATE_ENDPOINT = "/api/?type=op&cmd=<show><high-availability><state></state></high-availability></show>"
CREATE_ZONE_ENDPOINT = "/api/?type=config&action=set&xpath=/config/devices/entry[@name='localhost.localdomain']/vsys/entry[@name='vsys1']/zone/entry[@name='{}']&element=<layer3/>"
CREATE_MGMT_PROFILE_ENDPOINT = "/api/?type=config&action=set&xpath=/config/devices/entry[@name='localhost.localdomain']/network/profiles/interface-management-profile/entry[@name='{}']&element=<permitted-ip><member>10.0.0.0/8</member></permitted-ip><https>yes</https><ping>yes</ping><ssh>yes</ssh>"
CREATE_LOOPBACK_ENDPOINT = "/api/?type=config&action=set&xpath=/config/devices/entry[@name='localhost.localdomain']/network/interface/loopback/units/entry[@name='{}']&element=<ip><entry name='{}'/></ip><interface-management-profile>{}</interface-management-profile><zone>{}</zone>"
COMMIT_ENDPOINT = "/api/?type=commit&cmd=<commit></commit>"

def get_api_key(ip, username, password):
    url = f"https://{ip}{API_KEY_ENDPOINT.format(username, password)}"
    response = requests.get(url, verify=False)
    if response.status_code == 200:
        return response.text.split("<key>")[1].split("</key>")[0]
    return None

import xml.etree.ElementTree as ET

def check_ha_state(ip, api_key):
    url = f"https://{ip}{HA_STATE_ENDPOINT}"
    headers = {"X-PAN-KEY": api_key}
    response = requests.get(url, headers=headers, verify=False)
    
    if response.status_code == 200:
        try:
            # Parse the XML response
            root = ET.fromstring(response.text)
            
            # Check if HA is enabled
            enabled = root.find(".//enabled").text
            if enabled == "no":
                return "standalone"  # Device is not part of an HA pair
            
            # Get the local HA state
            local_state = root.find(".//local-info/state").text
            if local_state == "active":
                return "active"  # Device is active in HA pair
            elif local_state == "passive":
                return "passive"  # Device is passive in HA pair
            
            # If no state is found, return unknown
            return "unknown"
        except Exception as e:
            print(f"Error parsing HA state response from {ip}: {e}")
            return "unknown"
    else:
        print(f"Failed to query HA state from {ip}. Status code: {response.status_code}")
        return "unknown"

def create_mgmt_profile(ip, api_key, profile_name, whitelisted_jh_ip):
    url = f"https://{ip}/restapi/v10.1/Network/InterfaceManagementNetworkProfiles?name={profile_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@name": profile_name,
            "https": "yes",
            "ping": "yes",
            "permitted-ip": {
                "entry": [
                    {
                        "@name": f"{whitelisted_jh_ip}"
                    }
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)
    print(response.json())
    return response.status_code == 200

def create_loopback(ip, api_key, loopback_name, ip_address, profile_name):
    url = f"https://{ip}/restapi/v10.1/Network/LoopbackInterfaces?name={loopback_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@name": loopback_name,
            "ip": {
                "entry": [
                    {
                        "@name": ip_address
                    }
                ]
            },
            "interface-management-profile": profile_name
        }
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)
    return response.status_code == 200

def create_zone(ip, api_key, zone_name, loopback_name):
    url = f"https://{ip}/restapi/v10.1/Network/Zones?location=vsys&vsys=vsys1&name={zone_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@location": "vsys",
            "@name": zone_name,
            "network": {
                "layer3": {
                    "member": [
                        loopback_name
                    ]
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)
    return response.status_code == 200

def commit_changes(ip, api_key):
    url = f"https://{ip}/api/?type=commit&cmd=<commit></commit>"
    headers = {"X-PAN-KEY": api_key}
    response = requests.post(url, headers=headers, verify=False)
    return response.status_code == 200

def configure_device(ip, username, password, subnet, zone_name, profile_name, whitelisted_jh_ip):
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return ip, "Failed to get API key"
    
    ha_state = check_ha_state(ip, api_key)
    if ha_state == "passive":
        return ip, "Skipped (Passive HA device)"
    elif ha_state == "unknown":
        return ip, "Skipped (Unknown HA state)"
    
    if not create_mgmt_profile(ip, api_key, profile_name, whitelisted_jh_ip):
        return ip, "Failed to create management profile"

    # Find next available loopback interface and IP
    # This part is simplified and should be expanded based on your specific requirements
    loopback_name = "loopback.2"
    ip_address = str(subnet[1])
    
    if not create_loopback(ip, api_key, loopback_name, ip_address, profile_name):
        return ip, "Failed to create loopback interface"
    
    if not create_zone(ip, api_key, zone_name, loopback_name):
        return ip, "Failed to create zone"
    
    if not commit_changes(ip, api_key):
        return ip, "Failed to commit changes"
    
    return ip, "Success"

def main():
    whitelisted_jh_ip = '192.168.117.150'
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    
    print("Enter available /24 subnet (e.g., 192.168.1.0/24):")
    subnet_input = input()
    subnet = list(ip_network(subnet_input).hosts())
    
    print("Enter management IP addresses of devices (one per line, end with 'end'):")
    devices = []
    while True:
        ip = input()
        if ip.lower() == "end":
            break
        devices.append(ip)
    
    zone_name = "CUST-MGMT"
    profile_name = "CUST-MGMT-PROFILE"
    
    successful_devices = []
    failed_devices = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(configure_device, ip, username, password, subnet, zone_name, profile_name, whitelisted_jh_ip): ip for ip in devices}
        for future in concurrent.futures.as_completed(futures):
            ip, result = future.result()
            if result == "Success":
                successful_devices.append(ip)
            else:
                failed_devices.append((ip, result))
    
    print("\nSuccessful devices:")
    for ip in successful_devices:
        print(ip)
    
    print("\nFailed devices:")
    for ip, reason in failed_devices:
        print(f"{ip}: {reason}")

if __name__ == "__main__":
    main()
