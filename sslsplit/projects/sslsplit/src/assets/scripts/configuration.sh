#!/bin/bash
#
# Description:
# Settings file.
#
# Author: TW-D
# Version: 1.0
#

##
#---------------------------------------------------------------------------
readonly SSLSPLIT_DIRECTORY="/root/sslsplit/"
#---------------------------------------------------------------------------

##
#---------------------------------------------------------------------------
readonly OPENSSL_DIRECTORY="${SSLSPLIT_DIRECTORY}openssl/"
readonly PRIVATE_KEY_FILE="${OPENSSL_DIRECTORY}private-key.pem"
readonly OPENSSL_CNF_FILE="${OPENSSL_DIRECTORY}openssl.cnf"
readonly OPENSSL_CNF_CONTENT=$(cat <<EOF
#
# OpenSSL configuration file.
#

dir						= .

[ req ]
distinguished_name      = reqdn

[ reqdn ]

[ v3_ca ]
basicConstraints        = CA:TRUE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always,issuer:always
EOF
)
readonly CERTIFICATE_FILE="${OPENSSL_DIRECTORY}self-signed_certificate.crt"
readonly CERTIFICATE_SUBJECT="/O=SSLsplit Root CA/CN=SSLsplit Root CA/"
#---------------------------------------------------------------------------

##
#---------------------------------------------------------------------------
readonly RULES_DIRECTORY="${SSLSPLIT_DIRECTORY}rules/"
readonly IPTABLES_SSLSPLIT_RULES_FILE="${RULES_DIRECTORY}rules_sslsplit"
readonly IPTABLES_SSLSPLIT_RULES_CONTENT=$(cat <<EOF
##################################################################
# Certain packets are redirected to the local port 8080 and 8443 #
##################################################################

## Plain text HTTP traffic (80) is redirected to port 8080
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 8080

## SSL-based HTTPS traffic (443) is redirected to port 8443
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 8443

## IMAP over SSL (993), SMTP over SSL (465 and 587) is redirected to port 8443
iptables -t nat -A PREROUTING -p tcp --dport 465 -j REDIRECT --to-ports 8443
iptables -t nat -A PREROUTING -p tcp --dport 587 -j REDIRECT --to-ports 8443
iptables -t nat -A PREROUTING -p tcp --dport 993 -j REDIRECT --to-ports 8443

## WhatsApp (5222) is redirected to port 8080
iptables -t nat -A PREROUTING -p tcp --dport 5222 -j REDIRECT --to-ports 8080
EOF
)
#---------------------------------------------------------------------------

##
#---------------------------------------------------------------------------
readonly LOGS_DIRECTORY="${SSLSPLIT_DIRECTORY}logs/"
#---------------------------------------------------------------------------
