Troubleshooting BGP Issues on Check Point Firewalls
This guide provides a structured approach to diagnosing and resolving BGP-related issues on Check Point firewalls, including key concepts like the RouteD daemon, BGP states, common issues, commands, and scenarios.

1. RouteD Daemon Overview
The RouteD daemon is Check Point’s dynamic routing process responsible for managing protocols like BGP, OSPF, and RIP. It integrates with the Gaia OS kernel to update the firewall’s routing table based on peer advertisements.
Key Roles of RouteD:
    • Establishes and maintains BGP peer sessions.
    • Exchanges routing updates with neighbors.
    • Applies routing policies (e.g., route filtering, AS path prepending).
    • Communicates with the kernel to install best-path routes.
RouteD Status Checks:
bash
Copy
# Verify RouteD is running  
ps aux | grep routed  

# Check RouteD service status (Gaia CLI)  
bgp view  
routed -s  
Note: Ensure the dynamic routing license is enabled via cpconfig or the Gaia WebUI.

2. BGP States and Common Issues
BGP sessions transition through the following states. Understanding these helps pinpoint failures:
State
Description
Common Issues
Idle
Initial state; no resources allocated.
Misconfigured neighbor IP/AS, firewall blocking TCP 179, or RouteD not running.
Connect
Attempting to establish a TCP connection.
Network unreachability, ACLs blocking BGP, or incorrect source interface.
Active
Actively trying to connect if the passive (Connect) approach fails.
Persistent connectivity issues (e.g., routing loops, MTU mismatches).
OpenSent
TCP connection established; waiting for OPEN message from peer.
AS number mismatch, version incompatibility, or invalid BGP parameters.
OpenConfirm
OPEN message received; awaiting KEEPALIVE.
Authentication failures, timer mismatches (hold-time), or packet loss.
Established
Peering is active; routes are exchanged.
Route advertisement failures, flapping, or policy mismatches.

3. Common BGP Issues
A. Session Not Establishing
    • Causes: AS number mismatch, blocked TCP port 179, incorrect neighbor IP, or missing authentication.
    • Commands:
      bash
      Copy
      # Check BGP neighbors (from Gaia CLI)  
      bgp view  
      show ip bgp summary  
      
      # Verify connectivity to the peer  
      ping <peer-ip>  
      traceroute <peer-ip>  
B. Routes Not Advertised/Received
    • Causes: Missing network statements, route filters (prefix-lists/route-maps), or invalid next-hop.
    • Commands:
      bash
      Copy
      # Enter the routing shell  
      vtysh  
      
      # Check advertised/received routes  
      show ip bgp neighbors <peer-ip> advertised-routes  
      show ip bgp neighbors <peer-ip> received-routes  
C. Route Flapping
    • Causes: Unstable links, route oscillations, or misconfigured timers.
    • Commands:
      bash
      Copy
      # Monitor BGP transitions in logs  
      tail -f /var/log/messages | grep BGP  
      
      # Check flapping routes  
      show ip bgp flap-statistics  
D. High CPU Usage by RouteD
    • Causes: Large routing tables, excessive updates, or complex policies.
    • Commands:
      bash
      Copy
      # Identify CPU usage  
      top -p $(pgrep routed)  
      
      # Reduce logging verbosity if needed  
      routed -l debug  # Use cautiously in production  

4. Troubleshooting Commands Cheat Sheet
Command
Purpose
vtysh
Enter the routing configuration shell.
show ip bgp summary
List BGP neighbors and session status.
show ip bgp neighbors
Detailed peer status and counters.
show ip route bgp
View BGP-learned routes in the routing table.
clear ip bgp *
Reset all BGP sessions (use with caution).
bgp debug <peer-ip> events
Enable debug logs for a specific peer.
routed -s
Check RouteD status and version.

5. Scenario-Based Troubleshooting
Scenario 1: BGP Session Stuck in Active State
    1. Verify IP connectivity between peers (ping, traceroute).
    2. Check for ACLs/firewall rules blocking TCP 179 on intermediate devices.
    3. Validate BGP configuration:
       bash
       Copy
       bgp view  
       show run  
    4. Ensure the correct source interface is configured for the BGP peer.
Scenario 2: Routes Missing from Routing Table
    1. Confirm the route exists in the BGP table:
       bash
       Copy
       show ip bgp  
    2. Check for route filters (prefix-list, route-map).
    3. Verify network statements or redistribution settings.
Scenario 3: High RouteD Memory/CPU Usage
    1. Limit the number of prefixes received using prefix-list or maximum-prefix.
    2. Optimize route-maps to reduce complexity.
    3. Consider aggregating routes.

6. Logging and Diagnostics
    • Log Location: /var/log/messages (filter for BGP or ROUTED).
    • Enable debug logging (temporarily):
      bash
      Copy
      routed -l debug  
      tail -f /var/log/messages  
    • Collect troubleshooting data:
      bash
      Copy
      routed -d  # Generate a debug dump  

7. Best Practices
    • Use prefix-list and route-map to filter unnecessary routes.
    • Enable BGP authentication (md5 password).
    • Monitor sessions with tools like routed -s or SmartView Monitor.
    • Keep Gaia OS and BGP firmware updated.
