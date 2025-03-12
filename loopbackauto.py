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
            version_parts = full_version.split(".")
            major_minor = ".".join(version_parts[:2])  # e.g. "10.2"
            return major_minor
        except Exception as e:
            print(f"Error retrieving OS version: {e}")
            return "10.2"
    else:
        print(f"Failed to retrieve OS version from {ip}. Status code: {resp.status_code}")
        return "10.2"

def create_mgmt_profile(ip, api_key, os_version, profile_name, whitelisted_jh_ip):
    """
    Create/Update an Interface Management Profile named 'profile_name' that allows ping/https
    and whitelists 'whitelisted_jh_ip'.
    """
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

def create_loopback(ip, api_key, os_version, loopback_name, loopback_ip_cidr, profile_name):
    """
    Create the loopback interface (without assigning it to a zone).
    loopback_ip_cidr should be e.g. '10.10.10.10/32'.
    """
    # Some PAN-OS versions need a base "loopback" node
    try:
        url_init = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name=loopback"
        headers_init = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
        _ = requests.post(url_init, headers=headers_init, json={"entry": {}}, verify=False)
    except Exception as e:
        print(f"Ignoring exception creating base 'loopback' node: {e}")

    # Now POST the actual loopback interface
    url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name={loopback_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    payload = {
        "entry": {
            "@name": loopback_name,
            "ip": {
                "entry": [
                    {"@name": loopback_ip_cidr}
                ]
            },
            "interface-management-profile": profile_name
        }
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 200:
        return True

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
            # If multiple, pick the first
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

        # 5. PUT the updated zone
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

def update_default_vr_with_interface(ip, api_key, os_version, interface_name):
    """
    Adds 'interface_name' (e.g. 'loopback.109') to the 'default' virtual router.
    """
    base_url = f"https://{ip}/restapi/v{os_version}/Network/VirtualRouters?name=default"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}

    # 1. GET the default VR
    get_resp = requests.get(base_url, headers=headers, verify=False)
    if get_resp.status_code != 200:
        print(
            f"Failed to retrieve default VR on {ip}, status: {get_resp.status_code}, "
            f"resp: {get_resp.text}"
        )
        return False

    try:
        vr_data = get_resp.json()
        entry = vr_data["result"]["entry"]
        if isinstance(entry, list):
            entry = entry[0]

        # 2. Current list of interfaces
        vr_interfaces = entry.get("interface", {}).get("member", [])
        if isinstance(vr_interfaces, str):
            vr_interfaces = [vr_interfaces]

        if interface_name not in vr_interfaces:
            vr_interfaces.append(interface_name)

        # 3. Build updated VR definition
        updated_entry = {
            "@name": "default",
            "interface": {
                "member": vr_interfaces
            }
        }
        # Preserve other keys from 'entry'
        for key, val in entry.items():
            if key not in ["interface"]:
                updated_entry[key] = val

        # 4. PUT the updated VR
        put_resp = requests.put(base_url, headers=headers, json={"entry": updated_entry}, verify=False)
        if put_resp.status_code == 200:
            return True

        print(
            f"Failed to update default VR on {ip}, status: {put_resp.status_code}, "
            f"resp: {put_resp.text}"
        )
        return False

    except Exception as e:
        print(f"Error updating default VR on {ip}: {e}")
        return False

#
# UPDATED FUNCTION: BGP redist rule creation using the EXACT payload structure you specified.
#

def add_bgp_redist_rule(ip, api_key, os_version, loopback_cidr, vr_name="default"):
    """
    Creates or updates BGP 'redit-rules' in the VR named 'default'
    so that the rule's @name = loopback_cidr, address-family-identifier = "ipv4".

    Note: This overwrites 'redit-rules' with a single entry. If you want to preserve
    other entries, you'd first GET the current config and merge. However, this is the
    minimal approach the user requested, with the EXACT key "redit-rules".
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/VirtualRouters?name={vr_name}"
    headers = {
        "X-PAN-KEY": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "entry": {
            "@name": vr_name,
            "protocol": {
                "bgp": {
                    "redit-rules": {
                        "entry": [
                            {
                                "@name": loopback_cidr,
                                "address-family-identifier": "ipv4"
                            }
                        ]
                    }
                }
            }
        }
    }

    resp = requests.put(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 200:
        print(f"[{ip}] BGP redit-rules updated with @name={loopback_cidr}.")
        return True
    else:
        print(f"[{ip}] Failed to update redit-rules. Status: {resp.status_code}, Response: {resp.text}")
        return False

def commit_changes(ip, api_key):
    """
    Commit the changes using the XML API
    """
    url = f"https://{ip}/api/?type=commit&cmd=<commit></commit>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.post(url, headers=headers, verify=False)
    return resp.status_code == 200

def configure_device(ip, username, password, subnet, profile_name, whitelisted_jh_ip):
    """
    Configure a single device:
      1. Create mgmt profile
      2. Create loopback.109 with /32 mask from the second IP in 'subnet'
      3. Add loopback.109 to 'default' VR
      4. Create BGP 'redit-rules' entry with @name=the loopback /32
      5. Add loopback.109 to zone 'Untrust-L3'
      6. Commit
    """
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return ip, "Failed to get API key"
    
    ha_state = check_ha_state(ip, api_key)
    if ha_state == "passive":
        return ip, "Skipped (Passive HA device)"
    elif ha_state == "unknown":
        return ip, "Skipped (Unknown HA state)"

    os_version = get_os_version(ip, api_key)

    # 1. Mgmt Profile
    if not create_mgmt_profile(ip, api_key, os_version, profile_name, whitelisted_jh_ip):
        return ip, "Failed to create mgmt profile"
    
    # 2. Loopback
    loopback_name = "loopback.109"
    ip_with_cidr = f"{str(subnet[1])}/32"
    if not create_loopback(ip, api_key, os_version, loopback_name, ip_with_cidr, profile_name):
        return ip, "Failed to create loopback interface"

    # 3. VR
    if not update_default_vr_with_interface(ip, api_key, os_version, loopback_name):
        return ip, "Failed to add loopback to default VR"

    # 4. BGP redit-rule (with EXACT schema you demanded)
    if not add_bgp_redist_rule(ip, api_key, os_version, ip_with_cidr, vr_name="default"):
        return ip, "Failed to add BGP redit-rule"

    # 5. Zone
    if not update_zone_with_loopback(ip, api_key, os_version, "Untrust-L3", loopback_name):
        return ip, "Failed to update zone with loopback"

    # # 6. Commit
    # if not commit_changes(ip, api_key):
    #     return ip, "Failed to commit changes"
    
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
        ipaddr = input().strip()
        if ipaddr.lower() == "end":
            break
        devices.append(ipaddr)
    
    profile_name = "CUST-MGMT-PROFILE"

    successful_devices = []
    failed_devices = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(
                configure_device,
                ipaddr,
                username,
                password,
                subnet,
                profile_name,
                whitelisted_jh_ip
            ): ipaddr for ipaddr in devices
        }
        for fut in concurrent.futures.as_completed(future_map):
            ip_result, result_reason = fut.result()
            if result_reason == "Success":
                successful_devices.append(ip_result)
            else:
                failed_devices.append((ip_result, result_reason))
    
    print("\nSuccessful devices:")
    for ipaddr in successful_devices:
        print(ipaddr)
    
    print("\nFailed devices:")
    for ipaddr, reason in failed_devices:
        print(f"{ipaddr}: {reason}")

if __name__ == "__main__":
    main()
