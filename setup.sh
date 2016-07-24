#!/bin/sh

# Set up enviornment for development
export POLITI_HACK_CONFIG_PATH='./config.json'

# Install pip requirements
sudo pip3.5 install -r requirements.txt --upgrade
