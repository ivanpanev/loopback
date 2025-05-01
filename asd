create ltm monitor https SERVIM_HTTPS { adaptive disabled cipherlist DEFAULT compatibility enabled defaults-from /Common/https destination *:* interval 30 ip-dscp 0 partition Common recv none recv-disable none send "GET /servim/ws/ServiceImmatV3?wsdl\r\n" ssl-profile /Common/EAM_HTTPS_ssl_profile time-until-up 0 timeout 91 }


ltm monitor https SERVIM_HTTPS {
    adaptive disabled
    cipherlist DEFAULT
    compatibility enabled
    defaults-from /Common/https
    destination *:*
    interval 30
    ip-dscp 0
    partition INFOPRO_ETAI_34012
    recv none
    recv-disable none
    send "GET /servim/ws/ServiceImmatV3?wsdl\r\n"
    ssl-profile /INFOPRO_ETAI_34012/EAM_HTTPS_ssl_profile
    time-until-up 0
    timeout 91
}

