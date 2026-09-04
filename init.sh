#!/bin/bash

set -e # Exit on error

DEFAULT_UID=$(id -u)
DEFAULT_GID=$(id -g)

if ! command -v lockfile &>/dev/null; then
    if [ -t 0 ]; then
        read -rp "procmail is required for deployment lock mechanism. Install it now? [Y/n]: " INSTALL_PROCMAIL
        INSTALL_PROCMAIL=${INSTALL_PROCMAIL:-Y}

        if [[ "$INSTALL_PROCMAIL" =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y procmail
        else
            echo "Skipping procmail installation."
        fi
    else
        echo "procmail is required for deployment lock mechanism. Install it manually."
    fi
fi

# Create logs folder with permissions
echo "Updating folder permissions"
mkdir -p logs guilds
sudo chmod -R 777 logs guilds
sudo chown -R $DEFAULT_UID:$DEFAULT_GID logs/ guilds/

# Create network prometheus if not exists
if ! docker network inspect prometheus &>/dev/null; then
    echo "Creating network prometheus"
    docker network create prometheus
fi
