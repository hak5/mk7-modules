#!/bin/bash
#
# Description:
# Generate the SSL certificate authority and 
# private key for SSLsplit to use.
#
# Author: TW-D
# Version: 1.0
#

set -eo pipefail
source /pineapple/modules/sslsplit/assets/scripts/configuration.sh
set -u

cleanup() {
    set +e
    rm --recursive "${OPENSSL_DIRECTORY}" 2> /dev/null
    set -e
}

create_openssl_directory() {
    mkdir --parents "${OPENSSL_DIRECTORY}"
}

create_private_key() {
    openssl genrsa -out "${PRIVATE_KEY_FILE}" 2048
}

create_openssl_config() {
    touch "${OPENSSL_CNF_FILE}"
    echo "${OPENSSL_CNF_CONTENT}" > "${OPENSSL_CNF_FILE}"
}

create_certificate() { 
    openssl req -new -nodes -x509 -sha1 -out "${CERTIFICATE_FILE}" -key "${PRIVATE_KEY_FILE}" -config "${OPENSSL_CNF_FILE}" -extensions v3_ca -subj "${CERTIFICATE_SUBJECT}" -set_serial 0 -days 3650
}

launch_jobs() {
    cleanup
    create_openssl_directory
    create_private_key
    create_openssl_config
    create_certificate
}

if [ -d "${SSLSPLIT_DIRECTORY}" ] && [ -d "${OPENSSL_DIRECTORY}" ] && [ -f "${PRIVATE_KEY_FILE}" ] && [ -f "${OPENSSL_CNF_FILE}" ] && [ -f "${CERTIFICATE_FILE}" ]; then
    exit 0
else
    launch_jobs
fi