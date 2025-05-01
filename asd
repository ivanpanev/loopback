veselin.zhilkov@(vaas-etai0-lb-2683062-a)(cfg-sync In Sync)(Active)(/Common)(tmos)# 
veselin.zhilkov@(vaas-etai0-lb-2683062-a)(cfg-sync In Sync)(Active)(/Common)(tmos)# create ltm monitor https SERVIM_HTTPS { adaptive disabled cipherlist DEFAULT compatibility enabled defaults-from /Common/https destination *:* interval 30 ip-dscp 0 recv none recv-disable none send "GET /servim/ws/ServiceImmatV3?
Values:
  [enter value]
veselin.zhilkov@(vaas-etai0-lb-2683062-a)(cfg-sync In Sync)(Active)(/Common)(tmos)# create ltm monitor https SERVIM_HTTPS { adaptive disabled cipherlist DEFAULT compatibility enabled defaults-from /Common/https destination *:* interval 30 ip-dscp 0 recv none recv-disable none send "GET /servim/ws/ServiceImmatV3wsdl\r\n" ssl-profile /Common/EAM_HTTPS_ssl_profile time-until-up 0 timeout 91 }
[api-status-warning] ltm/monitor/https, properties : deprecated : cipherlist, compatibility
