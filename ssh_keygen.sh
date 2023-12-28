# Generating keys for `/ios` and `/verify_db pull`
docker exec -i rubbergod-bot-1 ash << EOF
set -e
SSH_DIR="/root/.ssh" # Everything runs as root inside the container
mkdir -p "\$SSH_DIR"
chmod 755 "\$SSH_DIR"
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "\$SSH_DIR"/leakcheck  1>/dev/null 2>&1
echo "y" | ssh-keygen -q -N "" -t ed25519 -f "\$SSH_DIR"/etc_passwd 1>/dev/null 2>&1
echo "command=\"/homes/eva/xl/xlogin00/rubbergod/leakcheck\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty" "\$(cat "\$SSH_DIR"/leakcheck.pub)"
echo "command=\"cat /etc/passwd\",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty" "\$(cat "\$SSH_DIR"/leakcheck.pub)"
EOF
# Now, run this script and append its output to merlin:~/.ssh/authorized_keys
