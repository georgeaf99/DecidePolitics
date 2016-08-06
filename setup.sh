#!/bin/sh

# Set up enviornment variables
export POLITI_HACK_CONFIG_PATH='./config.json'
export FLASK_APP='./gator/flask/__init__.py'

# Install pip requirements
sudo pip3.5 install -r requirements.txt --upgrade
