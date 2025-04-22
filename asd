---
# Executed once per GNID
# Delegation rules:
#   • *All* NetBox calls → 10.160.2.22 (netbox_delegate)
#   • Firewall tasks later will use role‑based delegate_host

- name: Initialise match list
  set_fact:
    ip_matches: []

# 1. Query NetBox for each role (sequentially)
- name: Query NetBox for GNID {{ gnid }} in role {{ role_id }}
  uri:
    url: "{{ netbox_base }}{{ role_matrix[role_id].endpoint }}/?role_id={{ role_id }}&cf_cmd_gnid={{ gnid }}"
    headers:
      Authorization: "Token {{ netbox_token }}"
      Accept: "application/json"
    validate_certs: no            # change back to 'yes' if your CA is trusted
    return_content: yes
  loop: "{{ role_matrix.keys() | list }}"
  loop_control:
    loop_var: role_id             # unique loop var for each iteration
    label: "role {{ role_id }}"
  delegate_to: "{{ netbox_delegate }}"    # delegate NetBox access to 10.160.2.22
  failed_when: false              # 0‑result lookups are not errors
  register: netbox_response       # register the response

# 2. Debug the NetBox API response
- name: Print NetBox API response for GNID {{ gnid }} and role {{ role_id }}
  debug:
    msg: "NetBox response for role {{ role_id }}: {{ netbox_response }}"

# 3. Collect results after all NetBox queries (sequentially)
- name: Collect NetBox hits
  set_fact:
    ip_matches: >-
      {{ ip_matches
         + (item.result.json.results | default([])
            | map('combine',
                  { 'role_id': item.result.invocation.module_args.url
                                 .split('role_id=')[1].split('&')[0] })
            | list) }}
  when: (item.result.json.count | default(0) | int) > 0
  loop: "{{ nb_results.results }}"
  loop_control:
    loop_var: item               # use `item` for each result object from the query
    label: "role {{ item.role_id }}"  # Label works because we've retained the `role_id`

# 4. Append to global list with the correct firewall delegate host
- name: Append matches to global firewalls list
  set_fact:
    firewalls: "{{ firewalls + new_entries }}"
  vars:
    new_entries: >-
      {{
        ip_matches
        | map('combine',
              {
                'gnid'         : gnid,
                'ip'           : (item.primary_ip4.address.split('/'))[0],
                'delegate_host': role_matrix[item.role_id].delegate
              }) | list
      }}
