#!/usr/bin/env bash
# Generate ssh keys for `/ios` and `/verify_db pull`

SSH_DIR="/root/.ssh" # Everything runs as root inside the container

# Exit on error
set -e

# Make sure the working dir is right
olddir="$(pwd)"
cd "$(dirname "$0")"
cd ..

printf "your xlogin00: "
read xlogin
printf "\n"

ssh_config="\
Host *
    IdentitiesOnly yes

Host eva merlin
    HostName %h.fit.vutbr.cz
    User $xlogin
    RequestTTY no

Host merlin
    ProxyCommand ssh -i /root/.ssh/nc_eva_merlin %r@eva\
"

# `ash` is not a mistake; Rubbergod Alpine does not have bash
docker exec -i rubbergod-bot-1 ash << EOF
set -e
mkdir -p "$SSH_DIR"
chmod 755 "$SSH_DIR"
echo "$ssh_config" > "$SSH_DIR"/config
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "$SSH_DIR"/leakcheck     1>/dev/null 2>&1
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "$SSH_DIR"/etc_passwd    1>/dev/null 2>&1
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "$SSH_DIR"/nc_eva_merlin 1>/dev/null 2>&1
echo "command=\"nc merlin 22\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty"                                             "\$(cat "$SSH_DIR"/nc_eva_merlin.pub)"
echo "command=\"cat /etc/passwd\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty"                                          "\$(cat "$SSH_DIR"/etc_passwd.pub)"
echo "command=\"/homes/eva/"${xlogin:0:2}"/${xlogin}/rubbergod/leakcheck\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty" "\$(cat "$SSH_DIR"/leakcheck.pub)"
EOF

# Restore the working dir
cd "$olddir"
echo "
# The script has run successfully.
# Now, append the above output to merlin:~/.ssh/authorized_keys.
# Don't forget to change the path of leakcheck script to your own.
# It is also advised to change the comment (last string) on all keys to something meaningful
# so you recognize it later.\
"
