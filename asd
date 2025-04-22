---
# Executed once per GNID

- name: Initialise match list
  set_fact:
    ip_matches: []

# 1. Async calls from the NetBox proxy host
- name: Query NetBox for GNID {{ gnid }} in role {{ role_id }}
  uri:
    url: "{{ netbox_base }}{{ role_matrix[role_id].endpoint }}/?role_id={{ role_id }}&cf_cmd_gnid={{ gnid }}"
    headers:
      Authorization: "Token {{ netbox_token }}"
      Accept: "application/json"
    validate_certs: no
    return_content: yes
  loop: "{{ role_matrix.keys() | list }}"
  loop_control:
    loop_var: role_id
  delegate_to: "{{ netbox_delegate }}"
  async: 3
  poll: 0
  #throttle: 3
  register: nb_async
  failed_when: false

- name: Wait for NetBox replies
  async_status:
    jid: "{{ item.ansible_job_id }}"
  register: nb_results
  until: nb_results.finished
  retries: 50
  delay: 1
  loop: "{{ nb_async.results }}"
  loop_control:
    label: "{{ item._ansible_item_label }}"
  delegate_to: "{{ netbox_delegate }}"

# 2. Collect every hit
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

# 3. Append to global list with the correct firewall delegate host
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










































{
  "started": 1,
  "finished": 1,
  "stdout": "",
  "stderr": "",
  "stdout_lines": [],
  "stderr_lines": [],
  "ansible_job_id": "2550675463.2430",
  "results_file": "/home/tier3.global.ip/.ansible_async/2550675463.2430",
  "content_length": "52",
  "cookies": {},
  "vary": "HX-Request, Cookie, origin",
  "x_content_type_options": "nosniff",
  "connection": "close",
  "content": "{\"count\":0,\"next\":null,\"previous\":null,\"results\":[]}",
  "json": {
    "count": 0,
    "previous": null,
    "results": [],
    "next": null
  },
  "msg": "Failed to template loop_control.label: 'dict object' has no attribute '_ansible_item_label'",
  "status": 200,
  "referrer_policy": "same-origin",
  "elapsed": 0,
  "invocation": {
    "module_args": {
      "force": false,
      "remote_src": false,
      "status_code": [
        200
      ],
      "owner": null,
      "body_format": "raw",
      "client_key": null,
      "group": null,
      "use_proxy": true,
      "unix_socket": null,
      "unsafe_writes": false,
      "serole": null,
      "setype": null,
      "follow_redirects": "safe",
      "unredirected_headers": [],
      "return_content": true,
      "method": "GET",
      "ca_path": null,
      "body": null,
      "timeout": 30,
      "src": null,
      "dest": null,
      "selevel": null,
      "force_basic_auth": false,
      "removes": null,
      "http_agent": "ansible-httpget",
      "use_gssapi": false,
      "url_password": null,
      "url": "https://netbox.gt-t.net/api/virtualization/virtual-machines/?role_id=226&cf_cmd_gnid=123123123123",
      "seuser": null,
      "client_cert": null,
      "creates": null,
      "headers": {
        "Accept": "application/json",
        "Authorization": "Token 518f3d24e8fe36f88faececc8837283c90d75f17"
      },
      "mode": null,
      "url_username": null,
      "attributes": null,
      "validate_certs": true
    }
  },
  "cross_origin_opener_policy": "same-origin",
  "content_type": "application/json",
  "date": "Tue, 22 Apr 2025 10:53:43 GMT",
  "x_frame_options": "SAMEORIGIN",
  "url": "https://netbox.gt-t.net/api/virtualization/virtual-machines/?role_id=226&cf_cmd_gnid=123123123123",
  "changed": false,
  "server": "nginx/1.20.1",
  "x_request_id": "30e4e09f-ff41-4554-b829-5ed552073c8d",
  "allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
  "redirected": false,
  "cookies_string": "",
  "_ansible_no_log": false,
  "attempts": 1,
  "item": {
    "ansible_job_id": "2550675463.2430",
    "started": 1,
    "failed": false,
    "finished": 0,
    "results_file": "/home/tier3.global.ip/.ansible_async/2550675463.2430",
    "changed": true,
    "failed_when_result": false,
    "role_id": "226",
    "ansible_loop_var": "role_id"
  },
  "ansible_loop_var": "item",
  "_ansible_delegated_vars": {
    "ansible_host": "10.160.2.22",
    "ansible_port": null,
    "ansible_user": "tier3.global.ip"
  }
}
