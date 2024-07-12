#!/bin/bash

DEFAULT_UID=$(id -u)
DEFAULT_GID=$(id -g)

# Create logs folder with permissions
echo "Updating logs folder permissions"
mkdir -p logs
sudo chmod -R 777 logs
sudo chown -R $DEFAULT_UID:$DEFAULT_GID logs/
