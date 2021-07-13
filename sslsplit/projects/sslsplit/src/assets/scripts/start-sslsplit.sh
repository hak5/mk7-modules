#!/bin/bash
#
# Description:
# Set IPTABLES rules and
# start SSLsplit
#
# Author: TW-D
# Version: 1.0
#

set -eo pipefail
source /pineapple/modules/sslsplit/assets/scripts/configuration.sh
set -u

create_rules_directory() {
    set +e
    mkdir "${RULES_DIRECTORY}" 2> /dev/null
    set -e
}

set_rules() {
    echo "1" > /proc/sys/net/ipv4/ip_forward

    iptables-save > "${RULES_DIRECTORY}rules_backup.txt"
    
    set +e

    iptables -X
    iptables -F
    iptables -t nat -F

    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT

    touch "${IPTABLES_SSLSPLIT_RULES_FILE}"
    echo "${IPTABLES_SSLSPLIT_RULES_CONTENT}" > "${IPTABLES_SSLSPLIT_RULES_FILE}"
    /bin/bash "${IPTABLES_SSLSPLIT_RULES_FILE}"

    iptables -t nat -A POSTROUTING -j MASQUERADE

    set -e
}

create_logs_directory() {
    set +e
    mkdir "${LOGS_DIRECTORY}" 2> /dev/null
    set -e
}

start_sslsplit() {
    local output_date
    output_date=$(date +%s)
    set +e
    killall sslsplit 2> /dev/null
    set -e
    sslsplit -D -l "${SSLSPLIT_DIRECTORY}connections.log" -L "${LOGS_DIRECTORY}output_${output_date}.log" -k "${PRIVATE_KEY_FILE}" -c "${CERTIFICATE_FILE}" ssl 0.0.0.0 8443 tcp 0.0.0.0 8080
}

launch_jobs() {
    create_rules_directory
    set_rules
    create_logs_directory
    start_sslsplit
}

if [ -d "${SSLSPLIT_DIRECTORY}" ] && [ -d "${OPENSSL_DIRECTORY}" ] && [ -f "${PRIVATE_KEY_FILE}" ] && [ -f "${CERTIFICATE_FILE}" ]; then
    echo "[DEBUG] Jobs launched" > /tmp/start-sslsplit.log
    launch_jobs
else
    exit 0
fi
