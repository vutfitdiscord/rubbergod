#!/bin/bash

set -e # Exit on error

DEFAULT_UID=$(id -u)
DEFAULT_GID=$(id -g)

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
