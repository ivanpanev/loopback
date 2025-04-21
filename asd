---

- name: Lookup device in NetBox and update PrimaryIP
  hosts: localhost
  gather_facts: no
  connection: local
  vars:
    netbox_base: "https://netbox.gt-t.net/api/"
    netbox_token: "0bd8f6b5bd34066ae603f1e6adda91b061f7f4ea"

  tasks:
    - name: Show original extra_vars
      debug:
        var: hostvars[inventory_hostname].extra_vars
      when: show_extra_vars | default(true)

    - name: Initialize primary_ip
      set_fact:
        primary_ip: ""

    # Check role_id=226 (virtualization)
    - name: Search for role_id=226 in virtualization
      uri:
        url: "{{ netbox_base }}virtualization/virtual-machines/?role_id=226&cf_cmd_gnid={{ extra_vars.RequestDetails.GNID }}"
        headers:
          Authorization: "Token {{ netbox_token }}"
          Accept: "application/json"
        validate_certs: yes
        return_content: yes
      register: result_226
      ignore_errors: yes
      when: not primary_ip

    - name: Set primary_ip if found in 226
      set_fact:
        primary_ip: "{{ (result_226.json.results[0].primary_ip4.address | split('/')).0 }}"
      when: 
        - not primary_ip
        - result_226 is succeeded
        - result_226.json.count > 0

    # Check role_id=478 (dcim)
    - name: Search for role_id=478 in dcim
      uri:
        url: "{{ netbox_base }}dcim/devices/?role_id=478&cf_cmd_gnid={{ extra_vars.RequestDetails.GNID }}"
        headers:
          Authorization: "Token {{ netbox_token }}"
          Accept: "application/json"
        validate_certs: yes
        return_content: yes
      register: result_478
      ignore_errors: yes
      when: not primary_ip

    - name: Set primary_ip if found in 478
      set_fact:
        primary_ip: "{{ (result_478.json.results[0].primary_ip4.address | split('/')).0 }}"
      when: 
        - not primary_ip
        - result_478 is succeeded
        - result_478.json.count > 0

    # Check role_id=136 (virtualization)
    - name: Search for role_id=136 in virtualization
      uri:
        url: "{{ netbox_base }}virtualization/virtual-machines/?role_id=136&cf_cmd_gnid={{ extra_vars.RequestDetails.GNID }}"
        headers:
          Authorization: "Token {{ netbox_token }}"
          Accept: "application/json"
        validate_certs: yes
        return_content: yes
      register: result_136
      ignore_errors: yes
      when: not primary_ip

    - name: Set primary_ip if found in 136
      set_fact:
        primary_ip: "{{ (result_136.json.results[0].primary_ip4.address | split('/')).0 }}"
      when: 
        - not primary_ip
        - result_136 is succeeded
        - result_136.json.count > 0

    # Check role_id=477 (virtualization)
    - name: Search for role_id=477 in virtualization
      uri:
        url: "{{ netbox_base }}virtualization/virtual-machines/?role_id=477&cf_cmd_gnid={{ extra_vars.RequestDetails.GNID }}"
        headers:
          Authorization: "Token {{ netbox_token }}"
          Accept: "application/json"
        validate_certs: yes
        return_content: yes
      register: result_477
      ignore_errors: yes
      when: not primary_ip

    - name: Set primary_ip if found in 477
      set_fact:
        primary_ip: "{{ (result_477.json.results[0].primary_ip4.address | split('/')).0 }}"
      when: 
        - not primary_ip
        - result_477 is succeeded
        - result_477.json.count > 0
