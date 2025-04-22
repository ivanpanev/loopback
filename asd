failed: [localhost] (item=None) => {"ansible_loop_var": "nb_res", "changed": false, "msg": "Failed to template loop_control.label: 'dict object' has no attribute 'role_id'", "nb_res": {"allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS", "ansible_job_id": "2673291490.3688", "ansible_loop_var": "nb_job", "attempts": 1, "changed": false, "connection": "close", "content": "{\"count\":0,\"next\":null,\"previous\":null,\"results\":[]}", "content_length": "52", "content_type": "application/json", "cookies": {}, "cookies_string": "", "cross_origin_opener_policy": "same-origin", "date": "Tue, 22 Apr 2025 11:08:47 GMT", "elapsed": 0, "failed": false, "finished": 1, "invocation": {"module_args": {"attributes": null, "body": null, "body_format": "raw", "ca_path": null, "client_cert": null, "client_key": null, "creates": null, "dest": null, "follow_redirects": "safe", "force": false, "force_basic_auth": false, "group": null, "headers": {"Accept": "application/json", "Authorization": "Token 518f3d24e8fe36f88fa…
failed: [localhost] (item=None) => {"ansible_loop_var": "nb_res", "changed": false, "msg": "Failed to template loop_control.label: 'dict object' has no attribute 'role_id'", "nb_res": {"allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS", "ansible_job_id": "378935891230.4075", "ansible_loop_var": "nb_job", "attempts": 1, "changed": false, "connection": "close", "content": "{\"count\":0,\"next\":null,\"previous\":null,\"results\":[]}", "content_length": "52", "content_type": "application/json", "cookies": {}, "cookies_string": "", "cross_origin_opener_policy": "same-origin", "date": "Tue, 22 Apr 2025 11:08:49 GMT", "elapsed": 0, "failed": false, "finished": 1, "invocation": {"module_args": {"attributes": null, "body": null, "body_format": "raw", "ca_path": null, "client_cert": null, "client_key": null, "creates": null, "dest": null, "follow_redirects": "safe", "force": false, "force_basic_auth": false, "group": null, "headers": {"Accept": "application/json", "Authorization": "Token 518f3d24e8fe36f88…
failed: [localhost] (item=None) => {"ansible_loop_var": "nb_res", "changed": false, "msg": "Failed to template loop_control.label: 'dict object' has no attribute 'role_id'", "nb_res": {"allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS", "ansible_job_id": "242747494473.4446", "ansible_loop_var": "nb_job", "attempts": 1, "changed": false, "connection": "close", "content": "{\"count\":0,\"next\":null,\"previous\":null,\"results\":[]}", "content_length": "52", "content_type": "application/json", "cookies": {}, "cookies_string": "", "cross_origin_opener_policy": "same-origin", "date": "Tue, 22 Apr 2025 11:08:51 GMT", "elapsed": 0, "failed": false, "finished": 1, "invocation": {"module_args": {"attributes": null, "body": null, "body_format": "raw", "ca_path": null, "client_cert": null, "client_key": null, "creates": null, "dest": null, "follow_redirects": "safe", "force": false, "force_basic_auth": false, "group": null, "headers": {"Accept": "application/json", "Authorization": "Token 518f3d24e8fe36f88…
failed: [localhost] (item=None) => {"ansible_loop_var": "nb_res", "changed": false, "msg": "Failed to template loop_control.label: 'dict object' has no attribute 'role_id'", "nb_res": {"allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS", "ansible_job_id": "904675602363.4877", "ansible_loop_var": "nb_job", "attempts": 1, "changed": false, "connection": "close", "content": "{\"count\":0,\"next\":null,\"previous\":null,\"results\":[]}", "content_length": "52", "content_type": "application/json", "cookies": {}, "cookies_string": "", "cross_origin_opener_policy": "same-origin", "date": "Tue, 22 Apr 2025 11:08:52 GMT", "elapsed": 0, "failed": false, "finished": 1, "invocation": {"module_args": {"attributes": null, "body": null, "body_format": "raw", "ca_path": null, "client_cert": null, "client_key": null, "creates": null, "dest": null, "follow_redirects": "safe", "force": false, "force_basic_auth": false, "group": null, "headers": {"Accept": "application/json", "Authorization": "Token 518f3d24e8fe36f88…



TASK [netbox_lookup : Collect NetBox hits] 



{
  "changed": false,
  "skip_reason": "Conditional result was False",
  "_ansible_no_log": false,
  "nb_res": {
    "started": 1,
    "finished": 1,
    "stdout": "",
    "stderr": "",
    "stdout_lines": [],
    "stderr_lines": [],
    "ansible_job_id": "2673291490.3688",
    "results_file": "/home/tier3.global.ip/.ansible_async/2673291490.3688",
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
    "msg": "OK (52 bytes)",
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
        "url": "https://netbox.gt-t.net/api/virtualization/virtual-machines/?role_id=226&cf_cmd_gnid=2498163",
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
        "validate_certs": false
      }
    },
    "cross_origin_opener_policy": "same-origin",
    "content_type": "application/json",
    "date": "Tue, 22 Apr 2025 11:08:47 GMT",
    "x_frame_options": "SAMEORIGIN",
    "url": "https://netbox.gt-t.net/api/virtualization/virtual-machines/?role_id=226&cf_cmd_gnid=2498163",
    "changed": false,
    "server": "nginx/1.20.1",
    "x_request_id": "70adffdc-21fd-44ae-8e77-9e7a25abe4ed",
    "allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS",
    "redirected": false,
    "cookies_string": "",
    "failed": false,
    "attempts": 1,
    "nb_job": {
      "ansible_job_id": "2673291490.3688",
      "started": 1,
      "failed": false,
      "finished": 0,
      "results_file": "/home/tier3.global.ip/.ansible_async/2673291490.3688",
      "changed": true,
      "failed_when_result": false,
      "role_id": "226",
      "ansible_loop_var": "role_id"
    },
    "ansible_loop_var": "nb_job"
  },
  "ansible_loop_var": "nb_res",
  "msg": "Failed to template loop_control.label: 'dict object' has no attribute 'role_id'"
}
