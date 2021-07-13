#!/bin/bash
#
# Description:
# Kill all SSLsplit processes and
# unset IPTABLES rules
#
# Author: TW-D
# Version: 1.0
#

set -eo pipefail
source /pineapple/modules/sslsplit/assets/scripts/configuration.sh
set -u

stop_sslsplit() {
    set +e
    killall sslsplit 2> /dev/null
    set -e
}

unset_rules() {
    set +e
    iptables -F
    iptables -X
    iptables -t nat -F
    iptables -t nat -X
    iptables -t mangle -F
    iptables -t mangle -X
    iptables -P INPUT ACCEPT
    iptables -P FORWARD ACCEPT
    iptables -P OUTPUT ACCEPT
    set -e
    iptables-restore < "${RULES_DIRECTORY}rules_backup.txt"
}

stop_sslsplit
unset_rules