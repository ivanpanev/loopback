---
# Executed once per GNID
# Delegation rules:
#   • *All* NetBox calls → 10.160.2.22 (netbox_delegate)
#   • Firewall tasks later will use role‑based delegate_host

- name: Initialise match list
  set_fact:
    ip_matches: []

# 1. Fire off async NetBox queries (one per role)
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
  async: 30
  poll: 0
  throttle: 10
  register: nb_async
  failed_when: false              # 0‑result lookups are not errors
  # Adding role_id explicitly into the results for future access
  set_fact:
    nb_async: "{{ nb_async.results | map('combine', {'role_id': role_id}) | list }}"

# 2. Wait for all async NetBox responses
- name: Wait for NetBox replies
  async_status:
    jid: "{{ nb_job.ansible_job_id }}"
  register: nb_results            # contains .results (one element per role)
  until: nb_results.finished
  retries: 60
  delay: 1
  loop: "{{ nb_async }}"
  loop_control:
    loop_var: nb_job              # keep track of individual job results
    label: "role {{ nb_job.role_id }}"  # This is now correctly accessed
  delegate_to: "{{ netbox_delegate }}"    # still delegate to the proxy host

# 3. Collect every hit (could be 0, 1, or 2 hits per role)
- name: Collect NetBox hits
  set_fact:
    ip_matches: >-
      {{ ip_matches
         + (nb_res.result.json.results | default([])
            | map('combine',
                  { 'role_id': nb_res.role_id })  # Access role_id directly
            | list) }}
  when: (nb_res.result.json.count | default(0) | int) > 0
  loop: "{{ nb_results.results }}"
  loop_control:
    loop_var: nb_res               # use `nb_res` for each result object from async_status
    label: "role {{ nb_res.role_id }}"  # Label works because we've retained the `role_id`

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
