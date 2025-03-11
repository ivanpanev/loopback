import requests
import json
import concurrent.futures
from getpass import getpass
from ipaddress import ip_network
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
        except:
            return "unknown"
    return "unknown"

def get_os_version(ip, api_key):
    url = f"https://{ip}/api/?type=op&cmd=<show><system><info></info></system></show>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.text)
            full_version = root.find(".//sw-version").text
            parts = full_version.split(".")
            major_minor = ".".join(parts[:2])  # e.g. "10.2"
            return major_minor
        except:
            return "10.2"
    return "10.2"

def get_default_route_interface(ip, api_key):
    url = f"https://{ip}/api/?type=op&cmd=<show><routing><route></route></routing></show>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code == 200:
        try:
            root = ET.fromstring(resp.text)
            entries = root.findall(".//entry")
            for e in entries:
                if e.find("destination").text == "0.0.0.0/0":
                    return e.find("interface").text
        except:
            return None
    return None

def find_zone_for_interface(ip, api_key, os_version, interface_name):
    url = f"https://{ip}/restapi/v{os_version}/Network/Zones?location=vsys&vsys=vsys1"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return None
    try:
        data = resp.json()
        entries = data["result"].get("entry", [])
        iface_strip = interface_name.strip()
        for z in entries:
            zone_name = z["@name"]
            layer3_members = z.get("network", {}).get("layer3", {}).get("member", [])
            if isinstance(layer3_members, str):
                layer3_members = [layer3_members]
            layer3_members = [m.strip() for m in layer3_members]
            if iface_strip in layer3_members:
                return zone_name
    except:
        pass
    return None

def create_or_update_loopback_and_subinterface(ip, api_key, os_version, subif_name, subif_ip, profile_name):
    """
    Creates or updates the parent 'loopback' interface object, ensuring it has
    a sub-interface named subif_name (e.g. 'loopback.2') with an IP, mgmt profile.
    """
    base_url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name=loopback"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}

    # 1) GET the existing 'loopback' interface object
    get_resp = requests.get(base_url, headers=headers, verify=False)

    if get_resp.status_code == 404:
        # Means the parent 'loopback' doesn't exist at all
        # We can create it from scratch with a POST
        payload = {
            "entry": {
                "@name": "loopback",
                "units": {
                    "entry": [
                        {
                            "@name": subif_name,
                            "ip": {
                                "entry": [
                                    {"@name": subif_ip}
                                ]
                            },
                            "interface-management-profile": profile_name
                        }
                    ]
                }
            }
        }
        post_resp = requests.post(base_url, headers=headers, json=payload, verify=False)
        if post_resp.status_code == 200:
            return True
        else:
            print(f"[ERROR] Failed to create parent 'loopback' with subif on {ip}. "
                  f"Status={post_resp.status_code}, Resp={post_resp.text}")
            return False

    elif get_resp.status_code == 200:
        # The parent 'loopback' object already exists
        try:
            existing_data = get_resp.json()["result"]["entry"]
            if isinstance(existing_data, list):
                # If for some reason multiple "loopback" entries, pick the first
                existing_data = existing_data[0]

            # Ensure there's a 'units' structure
            units = existing_data.get("units", {}).get("entry", [])
            if isinstance(units, dict):
                # If the firewall returns only one subif, it's a dict
                units = [units]

            # Find if subif_name is already in the 'units'
            found_subif = None
            for u in units:
                if u["@name"] == subif_name:
                    found_subif = u
                    break

            if not found_subif:
                # Create new sub-interface
                new_subif = {
                    "@name": subif_name,
                    "ip": {
                        "entry": [
                            {"@name": subif_ip}
                        ]
                    },
                    "interface-management-profile": profile_name
                }
                units.append(new_subif)
            else:
                # If sub-interface already exists, update mgmt profile or IP as needed
                # For simplicity, let's forcibly set the IP and mgmt profile
                found_subif["interface-management-profile"] = profile_name
                # Overwrite or merge IP if needed
                found_subif["ip"] = {
                    "entry": [
                        {"@name": subif_ip}
                    ]
                }

            # Build an updated payload
            updated_payload = {
                "entry": {
                    "@name": "loopback",
                    "units": {
                        "entry": units
                    }
                }
            }

            # 2) PUT the updated parent loopback object
            put_resp = requests.put(base_url, headers=headers, json=updated_payload, verify=False)
            if put_resp.status_code == 200:
                return True
            else:
                print(f"[ERROR] Failed to update existing 'loopback' with subif '{subif_name}' on {ip}. "
                      f"Status={put_resp.status_code}, Resp={put_resp.text}")
                return False

        except Exception as ex:
            print(f"[ERROR] Parsing existing loopback object on {ip}: {ex}")
            return False

    else:
        print(f"[ERROR] Unexpected response getting 'loopback' from {ip}. "
              f"Status={get_resp.status_code}, Resp={get_resp.text}")
        return False

def update_zone_with_loopback(ip, api_key, os_version, zone_name, loopback_name):
    """
    Same approach as before: GET the zone, add the sub-interface to member list, PUT back.
    """
    base_url = f"https://{ip}/restapi/v{os_version}/Network/Zones?location=vsys&vsys=vsys1&name={zone_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}

    get_resp = requests.get(base_url, headers=headers, verify=False)
    if get_resp.status_code != 200:
        print(f"Failed to retrieve zone '{zone_name}' on {ip}, status={get_resp.status_code}, resp={get_resp.text}")
        return False

    try:
        zone_data = get_resp.json()["result"]["entry"]
        if isinstance(zone_data, list):
            zone_data = zone_data[0]

        layer3_members = zone_data.get("network", {}).get("layer3", {}).get("member", [])
        if isinstance(layer3_members, str):
            layer3_members = [layer3_members]

        if loopback_name not in layer3_members:
            layer3_members.append(loopback_name)

        # Build updated zone definition
        zone_payload = {
            "entry": {
                "@name": zone_name,
                "@location": "vsys",
                "network": {
                    "layer3": {
                        "member": layer3_members
                    }
                }
            }
        }

        # PUT the updated zone
        put_resp = requests.put(base_url, headers=headers, json=zone_payload, verify=False)
        if put_resp.status_code == 200:
            return True
        else:
            print(f"Failed to update zone '{zone_name}' on {ip}, status={put_resp.status_code}, resp={put_resp.text}")
            return False

    except Exception as e:
        print(f"Error updating zone '{zone_name}' on {ip}: {e}")
        return False

def commit_changes(ip, api_key):
    url = f"https://{ip}/api/?type=commit&cmd=<commit></commit>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.post(url, headers=headers, verify=False)
    return resp.status_code == 200

def create_mgmt_profile(ip, api_key, os_version, profile_name, permitted_ip):
    """
    Basic example of creating/updating an interface management profile.
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
                    {"@name": permitted_ip}
                ]
            }
        }
    }
    resp = requests.post(url, headers=headers, json=payload, verify=False)
    if resp.status_code == 200:
        return True
    print(f"[ERROR] create_mgmt_profile on {ip}, status={resp.status_code}, resp={resp.text}")
    return False

def configure_device(ip, username, password, subnet, mgmt_profile, permitted_ip):
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return ip, "Failed to retrieve API key"

    ha_state = check_ha_state(ip, api_key)
    if ha_state == "passive":
        return ip, "Skipped (Passive HA device)"
    elif ha_state == "unknown":
        return ip, "Skipped (Unknown HA state)"

    os_version = get_os_version(ip, api_key)
    if not create_mgmt_profile(ip, api_key, os_version, mgmt_profile, permitted_ip):
        return ip, "Failed to create mgmt profile"

    default_iface = get_default_route_interface(ip, api_key)
    if not default_iface:
        return ip, "Could not find default route interface"

    untrust_zone = find_zone_for_interface(ip, api_key, os_version, default_iface)
    if not untrust_zone:
        return ip, f"Could not find zone containing interface {default_iface}"

    # 1) Create or update loopback parent + subif "loopback.2"
    loopback_subif = "loopback.2"
    loopback_ip = str(subnet[1])  # example usage
    if not create_or_update_loopback_and_subinterface(
        ip, api_key, os_version, loopback_subif, loopback_ip, mgmt_profile
    ):
        return ip, "Failed to create/modify loopback sub-interface"

    # 2) Add the sub-interface to the existing untrust zone
    if not update_zone_with_loopback(ip, api_key, os_version, untrust_zone, loopback_subif):
        return ip, "Failed to add loopback.2 to zone"

    # 3) Commit
    if not commit_changes(ip, api_key):
        return ip, "Failed to commit"

    return ip, "Success"


def main():
    username = input("Enter username: ")
    password = getpass("Enter password: ")

    print("Enter /24 subnet (e.g., 192.168.1.0/24):")
    subnet_input = input().strip()
    subnet_hosts = list(ip_network(subnet_input).hosts())

    print("Enter IP addresses of devices (one per line, end with 'end'):")
    devices = []
    while True:
        line = input().strip()
        if line.lower() == "end":
            break
        devices.append(line)

    mgmt_profile_name = "CUST-MGMT-PROFILE"
    whitelisted_jh_ip = "192.168.117.150"

    successful, failed = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(
                configure_device,
                ip,
                username,
                password,
                subnet_hosts,
                mgmt_profile_name,
                whitelisted_jh_ip
            ): ip for ip in devices
        }

        for fut in concurrent.futures.as_completed(future_map):
            ipaddr, result = fut.result()
            if result == "Success":
                successful.append(ipaddr)
            else:
                failed.append((ipaddr, result))

    print("\nSuccessful devices:")
    for s in successful:
        print(s)

    print("\nFailed devices:")
    for f, reason in failed:
        print(f"{f}: {reason}")

if __name__ == "__main__":
    main()
