---
- name: Get Device Facts
  hosts: HerbalCPE
  serial: 10
  gather_facts: no
  ignore_unreachable: true
  vars:
    ansible_port: 22
  tasks:
  - name: gather basic system info
    raw: get system status
    register: versionout

  - name: Version set
    set_fact: 
      version: "{{ versionout.stdout_lines | select('search', 'Version:') | map('regex_replace', '.*Version:\\s*', '') | first | split(' ') }}"

  - name: Get users
    raw: get system admin
    register: admindata

  - name: Filter user accounts
    set_fact: 
      adminlist: "{{ admindata.stdout_lines | select('search', 'name:') | map('regex_replace', '.*name:\\s*', '') | map('regex_replace', ' ', '')}}" 

  - name: Get Admin conifg
    raw: show system admin
    register: adminconfig

  - name: Generate config for every user
    set_fact: 
      trusthost: "{{ trusthost | default([]) + adminconfig.stdout_lines | regex_findall('edit \"' + item + '\"[\\s\\S]*?next') }}"
    loop: "{{ adminlist }}"

  - name: Make dictionary containing Username and Number of trusted hosts
    set_fact:
      turstnumber: "{{ turstnumber | default([]) + [{'Username': item | regex_search('edit.*?(\".*?\")', '\\1') | map('regex_replace', '\"', '' ) | first, 'TrushosttNum': item | regex_findall('trusthost') | length }] }}"
    loop: "{{ trusthost }}"

  - name: Save audit data to a file
    lineinfile:
      line: |
        Device {{ inventory_hostname }} (PON: {{ponid}}) with IP {{ ansible_host }} has following data:
          Model: {{version[0]}}
          Version: {{version[1]}}
          {% for line in turstnumber %}
        Username: {{ line.Username }}, Trusted Hosts Number: {{ line.TrushosttNum }}
          {% endfor %}

          {% for line in turstnumber %}
            {% if line.TrushosttNum < 1 %}
        Device {{ inventory_hostname }} with IP {{ ansible_host }} has account with no trusted hosts - Account name: {{ line.Username }}
            {% endif %}
          {% endfor %}

          ---------------------------------------------------------------------------------------------------------------------------------------------------
      insertafter: EOF
      dest: /home/panevii0/ansible/FortiConfigGet/Herbaloutput
      create: yes
    delegate_to: localhost




CPE-HERBA1-8547656-17877855	ansible_host=69.167.101.78 ponid=8547656
CPE-HERBA1-8550519-33708787	ansible_host=69.71.58.33 ponid=8550519
CPE-HERBA1-8574716-33709917	ansible_host=69.71.10.10 ponid=8574716
CPE-HERBA1-8574507-17984875	ansible_host=18.37.47.194 ponid=8574507
CPE-HERBA1-8574587-17985897	ansible_host=18.7.61.186 ponid=8574587
CPE-HERBA1-8574598-17985748	ansible_host=69.71.33.46 ponid=8574598
CPE-HERBA1-8576988-33709958	ansible_host=69.71.33.854 ponid=8576988
CPE-HERBA1-8595806-33090405	ansible_host=64.158.6.186 ponid=8595806
CPE-HERBA1-8598470-33106986	ansible_host=69.71.44.198 ponid=8598470
CPE-HERBA1-8600600-33710008	ansible_host=69.71.45.70 ponid=8600600
CPE-HERBA1-8607870-33151795	ansible_host=69.71.74.86 ponid=8607870
CPE-HERBA1-8677495-33891687	ansible_host=197.88.76.18 ponid=8677495
CPE-HERBA1-8678788-33898081	ansible_host=18.56.8.18 ponid=8678788
CPE-HERBA1-8678818-33898790	ansible_host=18.56.8.86 ponid=8678818
CPE-HERBA1-8679156-33899681	ansible_host=69.71.330.54 ponid=8679156
CPE-HERBA1-8679196-33899878	ansible_host=69.71.330.47 ponid=8679196
CPE-HERBA1-8651889-33759678	ansible_host=18.881.6.818 ponid=8651889
CPE-HERBA1-8655840-33780777	ansible_host=18.81.87.170 ponid=8655840
CPE-HERBA1-8667685-33487709	ansible_host=17.8.1.170 ponid=8667685
CPE-HERBA1-8664688-33478790	ansible_host=37.857.177.46 ponid=8664688
CPE-HERBA1-8679587-33509976	ansible_host=119.17.804.74 ponid=8679587
CPE-HERBA1-8681608-33588996	ansible_host=107.811.5.188 ponid=8681608
CPE-HERBA1-8688009-33797406	ansible_host=107.47.58.94 ponid=8688009
CPE-HERBA1-8685867-33547717	ansible_host=18.81.106.36 ponid=8685867
CPE-HERBA1-8657566-33798485	ansible_host=9.49.188.88 ponid=8717187





---
- name: Get auto-network settings
  hosts: HerbalCPE
  gather_facts: no
  serial: 10
  ignore_unreachable: true
  vars:
    ansible_port: 22

  tasks:
    - name: Show auto-network full-configuration
      raw: show full-configuration switch auto-network
      register: auto_net_output

    - name: Parse auto-network settings
      # This task extracts the 'set status' and 'set mgmt-vlan' lines if present
      set_fact:
        auto_network_status: >-
          {{
            (auto_net_output.stdout_lines | select('search', '^\\s*set status') | list | first | default(''))
            | regex_replace('.*set status\\s+(\\S+)', '\\1')
          }}
        auto_network_mgmt_vlan: >-
          {{
            (auto_net_output.stdout_lines | select('search', '^\\s*set mgmt-vlan') | list | first | default(''))
            | regex_replace('.*set mgmt-vlan\\s+(\\S+)', '\\1')
          }}

    - name: Save auto-network data to a file
      lineinfile:
        dest: /home/panevii0/ansible/FortiConfigGet/HerbalAutoNetworkOutput
        create: yes
        insertafter: EOF
        line: |
          Device {{ inventory_hostname }} (PON: {{ ponid }}) with IP {{ ansible_host }} auto-network:
            status      : {{ auto_network_status }}
            mgmt-vlan   : {{ auto_network_mgmt_vlan }}
          ----------------------------------------------------------------------------------------------------
      delegate_to: localhost

