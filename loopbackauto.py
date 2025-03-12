import requests
import json
import concurrent.futures
from getpass import getpass
from ipaddress import ip_network, ip_address, ip_interface
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
        except Exception:
            return "unknown"
    else:
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
        except Exception:
            return "10.2"
    else:
        return "10.2"

def get_loopback_interface(ip, api_key, os_version, loopback_name="loopback.109"):
    """
    Retrieves the 'loopback.109' interface config. Returns a dict or None if not found.
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name={loopback_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return None

    try:
        data = resp.json()
        entry = data["result"]["entry"]
        # If there's a list of entries, pick the first
        if isinstance(entry, list):
            entry = entry[0]
        return entry
    except Exception:
        return None

def update_loopback_interface(ip, api_key, os_version, loopback_name, new_ip):
    """
    Overwrites the loopback's IP list with the single new_ip/32 entry.
    new_ip is a string like '10.10.10.5/32'.
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/LoopbackInterfaces?name={loopback_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}

    # 1) Get the existing definition
    existing_entry = get_loopback_interface(ip, api_key, os_version, loopback_name)
    if not existing_entry:
        print(f"[{ip}] Loopback {loopback_name} not found or could not be fetched.")
        return False

    # 2) Overwrite the 'ip' list with our single new IP
    existing_entry["ip"] = {
        "entry": [
            {"@name": new_ip}
        ]
    }

    # 3) PUT the updated interface
    put_resp = requests.put(url, headers=headers, json={"entry": existing_entry}, verify=False)
    if put_resp.status_code == 200:
        print(f"[{ip}] Successfully updated {loopback_name} to {new_ip}.")
        return True
    else:
        print(f"[{ip}] Failed to update loopback {loopback_name}. Status: {put_resp.status_code}, Resp: {put_resp.text}")
        return False

def get_virtual_router(ip, api_key, os_version, vr_name="default"):
    """
    Retrieves the VR named 'default' and returns its 'entry' dict (or None if failed).
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/VirtualRouters?name={vr_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.get(url, headers=headers, verify=False)
    if resp.status_code != 200:
        return None
    try:
        vr_data = resp.json()
        entry = vr_data["result"]["entry"]
        if isinstance(entry, list):
            entry = entry[0]
        return entry
    except Exception:
        return None

def update_virtual_router(ip, api_key, os_version, vr_name, updated_entry):
    """
    Issues a PUT to overwrite the VR entry with 'updated_entry'.
    """
    url = f"https://{ip}/restapi/v{os_version}/Network/VirtualRouters?name={vr_name}"
    headers = {"X-PAN-KEY": api_key, "Content-Type": "application/json"}
    resp = requests.put(url, headers=headers, json={"entry": updated_entry}, verify=False)
    return resp

def update_bgp_redist_rule(ip, api_key, os_version, old_ip, new_ip, vr_name="default"):
    """
    In the given VR, find the BGP redist-rule with @name == old_ip/32, and rename/update it to new_ip/32.
    If none found, do nothing.

    NOTE: We preserve other VR config. 
    """
    vr_entry = get_virtual_router(ip, api_key, os_version, vr_name=vr_name)
    if not vr_entry:
        print(f"[{ip}] Could not fetch VR '{vr_name}'. Cannot update redist rule.")
        return False

    # Navigate to BGP redist-rules
    bgp = vr_entry.setdefault("protocol", {}).setdefault("bgp", {})
    redist_rules = bgp.setdefault("redist-rules", {}).setdefault("entry", [])

    found = False
    for rule in redist_rules:
        if rule.get("@name") == f"{old_ip}/32":
            # Update the rule name and address-family-identifier
            rule["@name"] = f"{new_ip}/32"
            rule["address-family-identifier"] = "ipv4"
            found = True
            break

    if not found:
        # If you do want to add a rule if old wasn't found, uncomment:
        # redist_rules.append({
        #     "@name": f"{new_ip}/32",
        #     "address-family-identifier": "ipv4"
        # })
        print(f"[{ip}] BGP redist rule '{old_ip}/32' not found, skipping update.")
        return True  # Not an error, just skip

    # Now we PUT the entire VR back
    put_resp = update_virtual_router(ip, api_key, os_version, vr_name, vr_entry)
    if put_resp.status_code == 200:
        print(f"[{ip}] Updated BGP redist rule: {old_ip}/32 -> {new_ip}/32 in VR '{vr_name}'.")
        return True
    else:
        print(f"[{ip}] Failed to update VR '{vr_name}'. Status: {put_resp.status_code}, Resp: {put_resp.text}")
        return False

def commit_changes(ip, api_key):
    """
    Commit the changes using the XML API (uncomment if you want an immediate commit).
    """
    url = f"https://{ip}/api/?type=commit&cmd=<commit></commit>"
    headers = {"X-PAN-KEY": api_key}
    resp = requests.post(url, headers=headers, verify=False)
    return resp.status_code == 200

def process_device(ip, username, password, new_ip):
    """
    1. Check if device is passive HA
    2. If loopback.109 has IP 172.30.254.2/32, rename it to new_ip/32
    3. If a BGP redist rule is found with @name=172.30.254.2/32, rename to new_ip/32
    4. Commit changes (optional)
    """
    api_key = get_api_key(ip, username, password)
    if not api_key:
        return ip, f"Failed to get API key"

    state = check_ha_state(ip, api_key)
    if state == "passive":
        return ip, "Skipped (Passive HA)"
    elif state == "unknown":
        return ip, "Skipped (Unknown HA State)"

    os_version = get_os_version(ip, api_key)

    # 1) Check if loopback.109 is assigned 172.30.254.2/32
    loopback_entry = get_loopback_interface(ip, api_key, os_version, "loopback.109")
    if not loopback_entry:
        return ip, "No loopback.109 found"

    ip_list = loopback_entry.get("ip", {}).get("entry", [])
    if not isinstance(ip_list, list):
        ip_list = [ip_list]

    # We look for 172.30.254.2/32
    found_old_ip = any(i.get("@name") == "172.30.254.2/32" for i in ip_list)
    if not found_old_ip:
        return ip, "No old IP found (172.30.254.2/32), skipping"

    new_ip_cidr = f"{new_ip}/32"

    # 2) Update loopback.109 to use the new IP
    if not update_loopback_interface(ip, api_key, os_version, "loopback.109", new_ip_cidr):
        return ip, "Failed updating loopback"

    # 3) Update BGP redist rule: rename old 172.30.254.2/32 => new_ip/32
    if not update_bgp_redist_rule(ip, api_key, os_version, "172.30.254.2", new_ip, vr_name="default"):
        return ip, "Failed updating BGP redist rule"

    # 4) Commit (optional – uncomment to do an immediate commit on each device)
    # if not commit_changes(ip, api_key):
    #     return ip, "Commit failed"

    return ip, "Success"

def main():
    username = input("Enter username: ").strip()
    password = getpass("Enter password: ").strip()

    # Input a larger /24 or /25 or /whatever for your unique IP addresses
    print("Enter an available subnet (e.g. 10.10.10.0/24):")
    subnet_input = input().strip()
    subnet_hosts = list(ip_network(subnet_input).hosts())

    print("Enter firewall management IPs, one per line. Type 'end' to finish.")
    devices = []
    while True:
        line = input().strip()
        if line.lower() == "end":
            break
        devices.append(line)

    # We'll just assign unique IPs from the start of the subnet
    # (Make sure you have at least as many hosts as devices)
    if len(devices) > len(subnet_hosts):
        print("ERROR: Not enough IP addresses in the subnet for all devices!")
        return

    # Map each device to a unique IP
    device_to_ip = {}
    for i, dev in enumerate(devices):
        device_to_ip[dev] = str(subnet_hosts[i])

    # Now run the updates in parallel
    success_list = []
    fail_list = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}
        for dev in devices:
            future = executor.submit(
                process_device,
                dev,
                username,
                password,
                device_to_ip[dev]
            )
            future_map[future] = dev

        for fut in concurrent.futures.as_completed(future_map):
            dev_ip, result_msg = fut.result()
            if result_msg == "Success":
                success_list.append(dev_ip)
            else:
                fail_list.append((dev_ip, result_msg))

    print("\n=== Results ===")
    print("Successful devices:")
    for d in success_list:
        print("  ", d)

    print("\nFailed devices:")
    for d, msg in fail_list:
        print(f"  {d}: {msg}")

if __name__ == "__main__":
    main()
