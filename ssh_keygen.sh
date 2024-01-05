#!/usr/bin/env bash
# Generating keys for `/ios` and `/verify_db pull`
printf "your xlogin00: "
read xlogin
# `ash` is not a mistake; Rubbergod Alpine does not have bash
docker exec -i rubbergod-bot-1 ash << EOF
set -e
SSH_DIR="/root/.ssh" # Everything runs as root inside the container
mkdir -p "\$SSH_DIR"
chmod 755 "\$SSH_DIR"
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "\$SSH_DIR"/leakcheck  1>/dev/null 2>&1
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "\$SSH_DIR"/etc_passwd 1>/dev/null 2>&1
echo "command=\"/homes/eva/"${xlogin:0:2}"/${xlogin}/rubbergod/leakcheck\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty" "\$(cat "\$SSH_DIR"/leakcheck.pub)"
echo "command=\"cat /etc/passwd\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty" "\$(cat "\$SSH_DIR"/leakcheck.pub)"
EOF
# Now, run this script and append its output to merlin:~/.ssh/authorized_keys.
# Don't forget to change the path of leakcheck script to your own.
# It is also advised to change the comment on both keys to something meaningful
# so you recognize it later.
