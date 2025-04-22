roles/netbox_lookup/vars/main.yml

---
# Map each NetBox device‑role ID to its Netbox API endpoint
# and the Ansible "delegate_to" host we must reach the FW through
role_matrix:
  "226":
    endpoint: "virtualization/virtual-machines"
    delegate: "localhost"
  "136":
    endpoint: "virtualization/virtual-machines"
    delegate: "localhost"
  "477":
    endpoint: "dcim/devices"
    delegate: "localhost"
  "478":
    endpoint: "dcim/devices"
    delegate: "jumphost-fw"     # change to your jump‑host FQDN














roles/netbox_lookup/tasks/main.yml

---
# Entry‑point for the role.  Runs ONCE on the AWX EE node.

# `gnid_block` is the *multi‑line text* Survey variable.
- name: Turn newline‑separated GNIDs into a clean list
  set_fact:
    gnid_list: >-
      {{ gnid_block.splitlines()
                   | map('trim')
                   | reject('equalto', '')       # drop blank lines
                   | list }}
    firewalls: []                                 # global accumulator

# Loop over the GNIDs by including the task‑file
- name: NetBox‑lookup each GNID
  include_tasks:
    file: lookup_one_gnid.yml
    apply:
      vars:
        gnid: "{{ item }}"
  loop: "{{ gnid_list }}"
  loop_control:
    label: "GNID {{ item }}"

# Make the list available to downstream workflow steps
- name: Expose firewalls fact to the workflow context
  set_stats:
    data:
      firewalls: "{{ firewalls }}"








roles/netbox_lookup/tasks/lookup_one_gnid.yml

---
# Executed ONCE for the current GNID.
# It may add *one or many* entries to the shared `firewalls` list.

- name: Start with an empty match list
  set_fact:
    ip_matches: []

# ── 1. Query NetBox for every allowed role (async to go faster) ───────────────
- name: Query NetBox for GNID {{ gnid }} in role {{ role_id }}
  uri:
    url: "{{ netbox_base }}{{ role_matrix[role_id].endpoint }}/?role_id={{ role_id }}&cf_cmd_gnid={{ gnid }}"
    headers:
      Authorization: "Token {{ netbox_token }}"
      Accept: "application/json"
    validate_certs: yes
    return_content: yes
  loop: "{{ role_matrix.keys() | list }}"
  loop_control:
    loop_var: role_id
  register: netbox_async
  async: 30
  poll: 0
  throttle: 10                # at most 10 calls in flight
  failed_when: false

- name: Wait for NetBox replies
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: netbox_results
  until: netbox_results.finished
  retries: 50
  delay: 1
  loop: "{{ netbox_async.results }}"
  loop_control:
    label: "{{ item._ansible_item_label }}"

# ── 2. Collect every hit (could be 0, 1 or 2) into ip_matches ────────────────
- name: Add any devices we found for this role
  set_fact:
    ip_matches: >-
      {{ ip_matches
         + (item.result.json.results | default([])
             | map('combine',
                   {
                     'role_id': item.result.invocation.module_args.url
                                  .split('role_id=')[1].split('&')[0] })
             | list) }}
  when: item.result.json.count | default(0) | int > 0
  loop: "{{ netbox_results.results }}"
  loop_control:
    label: "{{ item._ansible_item_label }}"

# ── 3. Append one dict per firewall to the GLOBAL list ───────────────────────
- name: Merge matches into the global `firewalls` fact
  set_fact:
    firewalls: "{{ firewalls + new_entries }}"
  vars:
    new_entries: >-
      {{
        ip_matches | map('combine',
          {
            'gnid'        : gnid,
            'ip'          : (item.primary_ip4.address.split('/'))[0],
            'delegate_host': role_matrix[item.role_id].delegate
          }) | list
      }}
















ha_check.yml

---
# ha_check.yml – second job‑template in AWX.
# Consumes the `firewalls` fact produced by netbox_lookup
# and outputs `ha_pairs` + `standalones` for later jobs.

- name: Discover HA topology of all resolved firewalls
  hosts: localhost
  gather_facts: false

  vars:
    firewalls: "{{ tower_workflow_job_template.inputs.firewalls }}"

  tasks:
    # ── Build a transient inventory of every firewall ─────────────────────────
    - name: Register dynamic hosts
      add_host:
        name: "{{ item.ip }}"
        ansible_host: "{{ item.ip }}"
        delegate_host: "{{ item.delegate_host }}"
        vars:
          gnid: "{{ item.gnid }}"
          role_id: "{{ item.role_id }}"
      loop: "{{ firewalls }}"

    # ── Gather HA facts in parallel ──────────────────────────────────────────
    - name: Get HA state from each firewall
      vars:
        ansible_network_os: paloaltonetworks.panos.panos
      panos_facts:
        gather_subset:
          - ha
      delegate_to: "{{ hostvars[item.ip].delegate_host }}"
      loop: "{{ firewalls }}"
      loop_control:
        loop_var: item
      register: ha_facts

    # ── Post‑process into pairs and stand‑alones ─────────────────────────────
    - name: Build ha_pairs and standalones lists
      set_fact:
        ha_pairs: >-
          {{
            ha_facts.results
            | selectattr('ansible_facts.panos_ha_enabled', 'defined')
            | groupby('ansible_facts.panos_ha_peer_ip')
            | map('list')
            | list
          }}
        standalones: >-
          {{
            ha_facts.results
            | rejectattr('ansible_facts.panos_ha_enabled', 'defined')
            | map(attribute='item')
            | list
          }}

    # ── Hand off to the next workflow node ──────────────────────────────────
    - name: Expose HA topology facts
      set_stats:
        data:
          ha_pairs: "{{ ha_pairs }}"
          standalones: "{{ standalones }}"

