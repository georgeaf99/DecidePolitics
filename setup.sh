#!/bin/sh

# Set up enviornment variables
export FLASK_APP='politi_hack.flask'
export POLITI_HACK_CONFIG_PATH='./config.json'
export PYTHONPATH=${PYTHONPATH}:./

# Install pip requirements
sudo pip3.5 install -r requirements.txt --upgrade
