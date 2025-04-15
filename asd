---
- name: PANORAMA Config Tasks
  block:
    - name: PANORAMA Create tag object 'GTT MDR'
      paloaltonetworks.panos.panos_tag_object:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        name: 'GTT MDR'
        color: 'chestnut'
        comments: 'GTT Managed Detection and Response'
      delegate_to: localhost

    - name: PANORAMA Gather all address objects
      paloaltonetworks.panos.panos_address_object:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        state: gathered
        gathered_filter: '*'
      register: gathered_address_objects
      delegate_to: localhost

    - name: PANORAMA Create address objects for unconfigured IPs
      paloaltonetworks.panos.panos_address_object:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        name: "MDR-BLOCKED-{{ ip | regex_replace('/', 'm') }}"
        value: "{{ ip }}"
        description: "Suspicious host identified by GTT Managed Detection and Response"
        tag: ['GTT MDR']
        commit: false
      loop: "{{ device.block_ips }}"
      loop_control:
        loop_var: ip
      when: device.block_ips | length > 0
      register: result_of_object_creation
      delegate_to: localhost

    - name: PANORAMA Gather list of new objects' names
      set_fact:
        relevant_address_objects: "{{ (gathered_address_objects.gathered | selectattr('value', 'in', device.block_ips) | map(attribute='name') | list) +
                                      (result_of_object_creation.results | selectattr('changed', 'equalto', true) | map(attribute='invocation.module_args.name') | list if result_of_object_creation is defined else []) }}"
      delegate_to: localhost

    - name: PANORAMA Gather existing object group
      paloaltonetworks.panos.panos_address_group:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        state: gathered
        gathered_filter: 'name == "GTT-MDR-Blocked-Addresses"'
      register: gathered_object_group
      delegate_to: localhost

    - name: Analyze existing group structure
      set_fact:
        main_group_exists: "{{ gathered_object_group.gathered | length > 0 }}"
        main_group_members: "{{ gathered_object_group.gathered[0].static_value | default([]) if main_group_exists else [] }}"
        main_group_addresses: "{{ main_group_members | reject('match', '^GTT-MDR-Blocked-Addresses-\\d+$') | list }}"
        existing_subgroups: "{{ main_group_members | select('match', '^GTT-MDR-Blocked-Addresses-\\d+$') | list }}"
      delegate_to: localhost

    - name: Calculate available space in main group
      set_fact:
        main_group_available: "{{ 1400 - (main_group_addresses | length) }}"
      when: main_group_exists
      delegate_to: localhost

    - name: Split new addresses between main group and subgroups
      set_fact:
        addresses_for_main: "{{ relevant_address_objects[0:main_group_available|int] | default([]) }}"
        addresses_for_subgroups: "{{ relevant_address_objects[main_group_available|int:] | default([]) }}"
      when: main_group_exists
      delegate_to: localhost

    - name: Update main group with new addresses
      paloaltonetworks.panos.panos_address_group:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        name: 'GTT-MDR-Blocked-Addresses'
        static_value: "{{ (main_group_addresses + addresses_for_main + existing_subgroups) | unique }}"
        description: "Suspicious hosts identified by GTT Managed Detection and Response"
        tag: ['GTT MDR']
        commit: false
      register: main_group_update
      when: 
        - main_group_exists
        - addresses_for_main | length > 0
      delegate_to: localhost

    - name: Handle subgroup creation and updates
      block:
        - name: Get latest subgroup info
          set_fact:
            latest_subgroup: "{{ (existing_subgroups | sort | last) | default(none) }}"
            latest_subgroup_suffix: "{{ (latest_subgroup | regex_replace('.*-(\\d+)$', '\\1')) | int if latest_subgroup else 0 }}"
          delegate_to: localhost

        - name: Gather latest subgroup members
          paloaltonetworks.panos.panos_address_group:
            provider:
              ip_address: '{{ device.panorama_mgmt_address }}'
              username: '{{ device.username }}'
              password: '{{ device.password }}'
            device_group: '{{ device.panorama_device_group }}'
            state: gathered
            gathered_filter: 'name == "{{ latest_subgroup }}"'
          register: current_subgroup
          when: latest_subgroup is not none
          delegate_to: localhost

        - name: Calculate subgroup available space
          set_fact:
            subgroup_available: "{{ 1400 - (current_subgroup.gathered[0].static_value | default([]) | length) }}"
          when: current_subgroup.gathered | length > 0
          delegate_to: localhost

        - name: Process subgroup updates
          block:
            - name: Update existing subgroup
              paloaltonetworks.panos.panos_address_group:
                provider:
                  ip_address: '{{ device.panorama_mgmt_address }}'
                  username: '{{ device.username }}'
                  password: '{{ device.password }}'
                device_group: '{{ device.panorama_device_group }}'
                name: "{{ latest_subgroup }}"
                static_value: "{{ current_subgroup.gathered[0].static_value + addresses_for_subgroups[0:subgroup_available|int] }}"
                description: "Updated subgroup with new blocked addresses"
                tag: ['GTT MDR']
                commit: false
              register: subgroup_update
              delegate_to: localhost

            - name: Calculate remaining addresses
              set_fact:
                remaining_addresses: "{{ addresses_for_subgroups[subgroup_available|int:] }}"
              delegate_to: localhost

            - name: Create new subgroups for remaining addresses
              paloaltonetworks.panos.panos_address_group:
                provider:
                  ip_address: '{{ device.panorama_mgmt_address }}'
                  username: '{{ device.username }}'
                  password: '{{ device.password }}'
                device_group: '{{ device.panorama_device_group }}'
                name: "GTT-MDR-Blocked-Addresses-{{ '%03d' % (latest_subgroup_suffix + 1 + loop.index) }}"
                static_value: "{{ remaining_addresses | slice(loop.index0*1400, (loop.index0+1)*1400) }}"
                description: "Auto-generated subgroup for blocked addresses"
                tag: ['GTT MDR']
                commit: false
              loop: "{{ range((remaining_addresses | length / 1400)|round(0, 'ceil')|int) }}"
              register: new_subgroups
              delegate_to: localhost

            - name: Update main group with new subgroups
              paloaltonetworks.panos.panos_address_group:
                provider:
                  ip_address: '{{ device.panorama_mgmt_address }}'
                  username: '{{ device.username }}'
                  password: '{{ device.password }}'
                device_group: '{{ device.panorama_device_group }}'
                name: 'GTT-MDR-Blocked-Addresses'
                static_value: "{{ main_group_members + new_subgroups.results | map(attribute='name') | list }}"
                commit: false
              when: new_subgroups is defined
              delegate_to: localhost

          when: 
            - addresses_for_subgroups | length > 0
            - latest_subgroup is not none
      when: 
        - main_group_exists
        - addresses_for_subgroups | length > 0

    - name: Handle initial group creation
      block:
        - name: Create main address group
          paloaltonetworks.panos.panos_address_group:
            provider:
              ip_address: '{{ device.panorama_mgmt_address }}'
              username: '{{ device.username }}'
              password: '{{ device.password }}'
            device_group: '{{ device.panorama_device_group }}'
            name: 'GTT-MDR-Blocked-Addresses'
            static_value: "{{ relevant_address_objects[0:1400] }}"
            description: "Suspicious hosts identified by GTT Managed Detection and Response"
            tag: ['GTT MDR']
            commit: false
          register: main_group_create
          delegate_to: localhost

        - name: Create initial subgroup if needed
          paloaltonetworks.panos.panos_address_group:
            provider:
              ip_address: '{{ device.panorama_mgmt_address }}'
              username: '{{ device.username }}'
              password: '{{ device.password }}'
            device_group: '{{ device.panorama_device_group }}'
            name: 'GTT-MDR-Blocked-Addresses-001'
            static_value: "{{ relevant_address_objects[1400:] }}"
            description: "Initial subgroup for blocked addresses"
            tag: ['GTT MDR']
            commit: false
          register: initial_subgroup
          when: relevant_address_objects | length > 1400
          delegate_to: localhost

        - name: Update main group with subgroup
          paloaltonetworks.panos.panos_address_group:
            provider:
              ip_address: '{{ device.panorama_mgmt_address }}'
              username: '{{ device.username }}'
              password: '{{ device.password }}'
            device_group: '{{ device.panorama_device_group }}'
            name: 'GTT-MDR-Blocked-Addresses'
            static_value: "{{ relevant_address_objects[0:1400] + ['GTT-MDR-Blocked-Addresses-001'] }}"
            commit: false
          when: initial_subgroup is defined
          delegate_to: localhost
      when: not main_group_exists

    - name: PANORAMA Gather existing security rules
      paloaltonetworks.panos.panos_security_rule:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_group: '{{ device.panorama_device_group }}'
        state: gathered
        gathered_filter: 'source_ip contains "GTT-MDR-Blocked-Addresses" and action == "deny"'
      register: gathered_rules
      delegate_to: localhost

    - name: PANORAMA Create security rule if missing
      paloaltonetworks.panos.panos_security_rule:
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        rulebase: pre-rulebase
        device_group: '{{ device.panorama_device_group }}'
        rule_name: 'GTT MDR Malicious Hosts'
        description: "Blocking all malicious hosts identified by GTT's MDR service."
        tag_name: ['GTT MDR']
        source_zone: ['any']
        destination_zone: ['any']
        source_ip: ['GTT-MDR-Blocked-Addresses']
        source_user: ['any']
        destination_ip: ['any']
        category: ['any']
        application: ['any']
        service: ['any']
        hip_profiles: ['any']
        action: 'drop'
        location: 'top'
        commit: false
      when: gathered_rules.gathered | length == 0
      register: result_of_rule_creation
      delegate_to: localhost

    - name: PANORAMA Commit changes
      paloaltonetworks.panos.panos_commit_panorama:
        admins: ['t3-admin']
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        device_groups: '{{ device.panorama_device_group }}'
        exclude_device_and_network: true
        description: 'Blocking MDR-identified malicious hosts.'
      when: >
        result_of_object_creation.changed or
        main_group_update.changed or
        subgroup_update.changed or
        new_subgroups.changed or
        main_group_create.changed or
        result_of_rule_creation.changed
      delegate_to: localhost

    - name: PANORAMA Push to devices
      paloaltonetworks.panos.panos_commit_push:
        admins: ['t3-admin']
        provider:
          ip_address: '{{ device.panorama_mgmt_address }}'
          username: '{{ device.username }}'
          password: '{{ device.password }}'
        style: 'device group'
        name: '{{ item }}'
        description: 'Blocking MDR-identified malicious hosts.'
        include_template: true
      loop: "{{ device.panorama_push_device_group is string | ternary([device.panorama_push_device_group], device.panorama_push_device_group) }}"
      when: >
        result_of_object_creation.changed or
        main_group_update.changed or
        subgroup_update.changed or
        new_subgroups.changed or
        main_group_create.changed or
        result_of_rule_creation.changed
      delegate_to: localhost

  rescue:
    - name: Error handling
      debug:
        msg: 'Configuration failed. Check previous tasks for errors.'
