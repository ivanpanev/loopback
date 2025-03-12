import requests
import json
import concurrent.futures
from getpass import getpass
from ipaddress import ip_network, ip_address
import xml.etree.ElementTree as ET

# Disable SSL warnings (not recommended for production)
requests.packages.urllib3.disable_warnings()

MAX_WORKERS = 10

def get_api_key(ip, username, password):
    url = f"https://{ip}/api/?type=keygen&user={username}&password={password}"
    resp = requests.get(url, verify=False)
    if resp.status_code == 200 and "<key>" in resp.text:
        return resp.text.split("<key>")[1].split("</key>")[0]
    return None

def check_ha_state(ip, api_key):
    url = f"https://{ip}/api/?type=op&cmd=<show><high-availability><state></state></high-availability></show>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.text)
            enabled = root.find(".//enabled").text
            if enabled == "no":
                return "standalone"
            local_state = root.find(".//local-info/state").text
            if local_state in ("active", "active-primary"):
                return "active"
            elif local_state == "passive":
                return "passive"
            return "unknown"
        except Exception as e:
            print(f"Error parsing HA state response from {ip}: {e}")
            return "unknown"
    else:
        print(f"Failed to query HA state from {ip}. Status code: {resp.status_code}")
        return "unknown"

def get_os_version(ip, api_key):
    url = f"https://{ip}/api/?type=op&cmd=<show><system><info></info></system></show>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.text)
            full_version = root.find(".//sw-version").text  # e.g. "10.2.3-h4"
            # Extract "major.minor"
            version_parts = full_version.split(".")
            major_minor = ".".join(version_parts[:2])  # "10.2"
            return major_minor
        except Exception as e:
            print(f"Error retrieving OS version: {e}")
            return "10.2"
    else:
        print(f"Failed to retrieve OS version from {ip}. Status code: {resp.status_code}")
        return "10.2"

def get_default_route_interface(ip, api_key):
    url = f"https://{ip}/api/?type=op&cmd=<show><routing><route></route></routing></show>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.get(url, headers=headers, verify=False)
    print("Routing:")
    print(resp.json())
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.text)
            routes = root.findall(".//entry")
            for r in routes:
                destination = r.find("destination").text
                if destination == "0.0.0.0/0":
                    iface = r.find("interface").text
                    return iface
        except Exception as e:
            print(f"Error parsing route table for {ip}: {e}")
            return None
    return None

def find_zone_for_interface(ip, api_key, os_version, interface_name):
    """
    Returns the zone name that contains 'interface_name' in the zone's layer3 member list.
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/Zones?location=vsys&vsys=vsys1"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        print(f"Failed to retrieve zone info from {ip}. Status: {resp.status_code}")
        return None
    try:
        data = resp.json()
        # The zones are typically in data["result"]["entry"]
        entries = data["result"].get("entry", [])
        iface_stripped = interface_name.strip()
        for z in entries:
            zone_name = z["@name"]
            layer3_members = z.get("network", {}).get("layer3", {}).get("member", [])
            if isinstance(layer3_members, str):
                layer3_members = [layer3_members]
            # strip each item
            layer3_stripped = [m.strip() for m in layer3_members]
            if iface_stripped in layer3_stripped:
                return zone_name
    except Exception as e:
        print(f"Error parsing zone info for {ip}: {e}")
    return None

def create_mgmt_profile(ip, api_key, os_version, profile_name, whitelisted_jh_ip):
    url = f"https://{ip}/restapi/v{os_version}/Network/InterfaceManagementNetworkProfiles?name={profile_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@name": profile_name,
            "https": "yes",
            "ping": "yes",
            "permitted-ip": {
                "entry": [
                    {"@name": str(whitelisted_jh_ip)}
                ]
            }
        }
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 200:
        return True
    print(f"Failed to create mgmt profile on {ip}, status: {resp.status_code}, response: {resp.text}")
    return False

def create_loopback(ip, api_key, os_version, loopback_name, loopback_ip, profile_name):
    """
    Create the loopback interface (without assigning a zone).
    """
    try:
        url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name=loopback"
        headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json",}
        payload = {
            "entry": {}
        }
        
        resp = requests.post(url, headers=headers, json=payload, verify=False)
    except Exception as e:
        print(f"Exception: {e}")
        
    url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name={loopback_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@name": loopback_name,
            "ip": {
                "entry": [
                    {"@name": loopback_ip}
                ]
            },
            "interface-management-profile": profile_name
        }
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)

    if resp.status_code == 200:
        return True
    else:
        print(f"Failed to create loopback '{loopback_name}' on {ip}, status: {resp.status_code}, response: {resp.text}")
        return False

def update_zone_with_loopback(ip, api_key, os_version, zone_name, loopback_name):
    """
    Fetch the zone object, add 'loopback_name' to its member list, and PUT it back.
    """
    base_url = f"https://{ip}/restapi/v{os_version}/Network/Zones?location=vsys&vsys=vsys1&name={zone_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    
    # 1. Retrieve the zone definition
    get_resp = requests.get(base_url, headers=headers, verify=False)
    if get_resp.status_code != 200:
        print(
            f"Failed to retrieve zone '{zone_name}' info from {ip}, "
            f"status: {get_resp.status_code}, resp: {get_resp.text}"
        )
        return False

    try:
        zone_data = get_resp.json()
        entry = zone_data["result"]["entry"]
        if not isinstance(entry, dict):
            # If there's more than one zone returned with the same name (rare),
            # just pick the first one.
            entry = entry[0]

        # 2. Current list of layer3 members
        layer3_members = entry.get("network", {}).get("layer3", {}).get("member", [])
        if isinstance(layer3_members, str):
            layer3_members = [layer3_members]

        # 3. Add the new loopback if not already present
        if loopback_name not in layer3_members:
            layer3_members.append(loopback_name)

        # 4. Build the updated zone definition
        updated_entry = {
            "@name": zone_name,
            "@location": "vsys",
            "network": {
                "layer3": {
                    "member": layer3_members
                }
            }
        }

        # 5. PUT the updated zone definition
        put_resp = requests.put(base_url, headers=headers, json={"entry": updated_entry}, verify=False)
        if put_resp.status_code == 200:
            return True
        else:
            print(
                f"Failed to update zone '{zone_name}' on {ip}, "
                f"status: {put_resp.status_code}, resp: {put_resp.text}"
            )
            return False

    except Exception as e:
        print(f"Error updating zone '{zone_name}' on {ip}: {e}")
        return False

def commit_changes(ip, api_key):
    url = f"https://{ip}/api/?type=commit&cmd=<commit></commit>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.post(url, headers=headers, verify=False)
    return resp.status_code == 200

def configure_device(ip, username, password, subnet, profile_name, whitelisted_jh_ip):
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return ip, "Failed to get API key"
    
    ha_state = check_ha_state(ip, api_key)
    if ha_state == "passive":
        return ip, "Skipped (Passive HA device)"
    elif ha_state == "unknown":
        return ip, "Skipped (Unknown HA state)"

    os_version = get_os_version(ip, api_key)

    # 1. Create/update mgmt profile
    if not create_mgmt_profile(ip, api_key, os_version, profile_name, whitelisted_jh_ip):
        return ip, "Failed to create mgmt profile"
    
    # # 2. Identify the default-route interface & corresponding zone
    # default_if = get_default_route_interface(ip, api_key)
    # if not default_if:
    #     return ip, "Could not find default route interface"
    # untrust_zone = find_zone_for_interface(ip, api_key, os_version, default_if)
    # if not untrust_zone:
    #     return ip, f"Could not find zone containing interface '{default_if}' (default route)."

    # 3. Create the loopback (without assigning a zone)
    loopback_name = "loopback.109"
    loopback_ip = str(subnet[1])  # take the second IP in the subnet
    if not create_loopback(ip, api_key, os_version, loopback_name, loopback_ip, profile_name):
        return ip, "Failed to create loopback interface"

    untrust_zone = "Untrust-L3"
    # 4. Add the loopback into the untrust zone
    if not update_zone_with_loopback(ip, api_key, os_version, untrust_zone, loopback_name):
        return ip, "Failed to update zone with loopback"

    # 5. Commit changes
    if not commit_changes(ip, api_key):
        return ip, "Failed to commit changes"
    
    return ip, "Success"

def main():
    whitelisted_jh_ip = '192.168.117.150'
    username = input("Enter username: ")
    password = getpass("Enter password: ")
    
    print("Enter available /24 subnet (e.g., 192.168.1.0/24):")
    subnet_input = input().strip()
    subnet = list(ip_network(subnet_input).hosts())
    
    print("Enter management IP addresses of devices (one per line, end with 'end'):")
    devices = []
    while True:
        ip = input().strip()
        if ip.lower() == "end":
            break
        devices.append(ip)
    
    profile_name = "CUST-MGMT-PROFILE"

    successful_devices = []
    failed_devices = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(
                configure_device,
                ip,
                username,
                password,
                subnet,
                profile_name,
                whitelisted_jh_ip
            ): ip for ip in devices
        }
        for fut in concurrent.futures.as_completed(future_map):
            ip_addr, result = fut.result()
            if result == "Success":
                successful_devices.append(ip_addr)
            else:
                failed_devices.append((ip_addr, result))
    
    print("\nSuccessful devices:")
    for ip in successful_devices:
        print(ip)
    
    print("\nFailed devices:")
    for ip, reason in failed_devices:
        print(f"{ip}: {reason}")

if __name__ == "__main__":
    main()
