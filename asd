---
- name: PANORAMA Config Tasks
  block:
    - name: Create tag object 'GTT MDR'
      paloaltonetworks.panos.panos_tag_object:
        provider: "{{ panorama_provider }}"
        device_group: "{{ device_group }}"
        name: 'GTT MDR'
        color: 'chestnut'
        comments: 'GTT Managed Detection and Response'
      delegate_to: localhost

    - name: Gather all address objects
      paloaltonetworks.panos.panos_address_object:
        provider: "{{ panorama_provider }}"
        device_group: "{{ device_group }}"
        state: gathered
        gathered_filter: '*'
      register: gathered_address_objects
      delegate_to: localhost

    - name: Create new address objects
      paloaltonetworks.panos.panos_address_object:
        provider: "{{ panorama_provider }}"
        device_group: "{{ device_group }}"
        name: "MDR-BLOCKED-{{ ip | regex_replace('/', 'm') }}"
        value: "{{ ip }}"
        description: "Suspicious host identified by GTT MDR"
        tag: ['GTT MDR']
        commit: false
      loop: "{{ block_ips }}"
      loop_control:
        loop_var: ip
      register: object_creation
      delegate_to: localhost

    - name: Compile relevant object names
      set_fact:
        new_objects: "{{ object_creation.results | selectattr('changed', 'equalto', true) | map(attribute='invocation.module_args.name') | list }}"
        existing_objects: "{{ gathered_address_objects.gathered | selectattr('value', 'in', block_ips) | map(attribute='name') | list }}"
        relevant_objects: "{{ existing_objects + new_objects }}"
      delegate_to: localhost

    - name: Gather main group info
      paloaltonetworks.panos.panos_address_group:
        provider: "{{ panorama_provider }}"
        device_group: "{{ device_group }}"
        state: gathered
        gathered_filter: 'name == "GTT-MDR-Blocked-Addresses"'
      register: main_group
      delegate_to: localhost

    - name: Initialize group structure
      set_fact:
        main_group_exists: "{{ main_group.gathered | length > 0 }}"
        current_members: "{{ main_group.gathered[0].static_value | default([]) if main_group_exists else [] }}"
        address_objects: "{{ current_members | reject('match', subgroup_pattern) | list }}"
        subgroups: "{{ current_members | select('match', subgroup_pattern) | list }}"
        subgroup_pattern: '^GTT-MDR-Blocked-Addresses-\\d{3}$'
      delegate_to: localhost

    - name: Find latest subgroup
      block:
        - name: Extract subgroup numbers
          set_fact:
            subgroup_numbers: "{{ subgroups | map('regex_replace', subgroup_pattern, '\\1') | map('int') | list }}"
        
        - name: Determine latest subgroup
          set_fact:
            latest_subgroup: "GTT-MDR-Blocked-Addresses-{{ '%03d' % (subgroup_numbers | max) }}"
            next_subgroup_num: "{{ (subgroup_numbers | max) + 1 }}"
          when: subgroup_numbers | length > 0
        
        - name: Set initial subgroup
          set_fact:
            latest_subgroup: ""
            next_subgroup_num: 1
          when: subgroup_numbers | length == 0
      when: main_group_exists
      delegate_to: localhost

    - name: Migrate existing addresses to subgroups
      block:
        - name: Get current subgroup capacity
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            state: gathered
            gathered_filter: 'name == "{{ latest_subgroup }}"'
          register: subgroup_info
          when: latest_subgroup != ""
          delegate_to: localhost

        - name: Calculate migration batches
          set_fact:
            subgroup_capacity: "{{ 1400 - (subgroup_info.gathered[0].static_value | default([]) | length) }}"
            migrate_to_existing: "{{ address_objects[0:subgroup_capacity] }}"
            migrate_to_new: "{{ address_objects[subgroup_capacity:] }}"
          when: latest_subgroup != ""
          delegate_to: localhost

        - name: Update existing subgroup
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "{{ latest_subgroup }}"
            static_value: "{{ subgroup_info.gathered[0].static_value + migrate_to_existing }}"
            commit: false
          when: latest_subgroup != "" and migrate_to_existing | length > 0
          delegate_to: localhost

        - name: Create new subgroups for remaining
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "GTT-MDR-Blocked-Addresses-{{ '%03d' % (next_subgroup_num + loop.index0) }}"
            static_value: "{{ migrate_to_new | slice(loop.index0*1400, (loop.index0+1)*1400) }}"
            commit: false
          loop: "{{ range((migrate_to_new | length / 1400)|round(0, 'ceil')|int) }}"
          register: new_subgroups
          delegate_to: localhost

        - name: Clean main group
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "GTT-MDR-Blocked-Addresses"
            static_value: "{{ subgroups + [latest_subgroup] + (new_subgroups.results | map(attribute='name') | list }}"
            commit: false
          delegate_to: localhost
      when: 
        - main_group_exists
        - address_objects | length > 0
      delegate_to: localhost

    - name: Process new addresses
      block:
        - name: Get current subgroup state
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            state: gathered
            gathered_filter: 'name == "{{ latest_subgroup }}"'
          register: current_subgroup
          when: latest_subgroup != ""
          delegate_to: localhost

        - name: Calculate available space
          set_fact:
            available_space: "{{ 1400 - (current_subgroup.gathered[0].static_value | default([]) | length) }}"
          when: latest_subgroup != ""
          delegate_to: localhost

        - name: Add to existing subgroup
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "{{ latest_subgroup }}"
            static_value: "{{ current_subgroup.gathered[0].static_value + relevant_objects[0:available_space] }}"
            commit: false
          when: latest_subgroup != "" and available_space > 0
          delegate_to: localhost

        - name: Create new subgroups for remaining
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "GTT-MDR-Blocked-Addresses-{{ '%03d' % (next_subgroup_num + loop.index0) }}"
            static_value: "{{ relevant_objects[available_space|int:] | slice(loop.index0*1400, (loop.index0+1)*1400) }}"
            commit: false
          loop: "{{ range((relevant_objects | length / 1400)|round(0, 'ceil')|int) }}"
          register: final_subgroups
          delegate_to: localhost

        - name: Update main group
          paloaltonetworks.panos.panos_address_group:
            provider: "{{ panorama_provider }}"
            device_group: "{{ device_group }}"
            name: "GTT-MDR-Blocked-Addresses"
            static_value: "{{ subgroups + [latest_subgroup] + (final_subgroups.results | map(attribute='name') | list }}"
            commit: false
          delegate_to: localhost
      delegate_to: localhost

    # Security rule and commit tasks remain unchanged from original

  rescue:
    - debug:
        msg: "Configuration failed. Check previous tasks for errors."
