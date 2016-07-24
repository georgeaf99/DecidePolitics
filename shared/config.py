import json
import os

# Static variables for easy access
MAX_TWILIO_MSG_SIZE  = 1600
SERVICE_PHONE_NUMBER = "+18554164150"

# Environment variables
POLITI_HACK_CONFIG_PATH = 'POLITI_HACK_CONFIG_PATH'

# This is just a template, the actual config is loaded from disk on startup,
# then overwrites the below data.
# Most config changes should occur in the json config file, NOT here.
store = {
    "api_host": {
        "name": "localhost",
        "bind_port": 8000,
        "recv_port": 8000,
    },
    "dynamodb": {
        "access_key": None,
        "secret_key": None,
        "endpoint": {
            "hostname": "localhost",
            "port": 8040,
        },
    },
    "google": {
        "api_key": None,
    },
    "sunlight": {
        "api_key": None
    },
    "twilio": {
        "account_sid": None,
        "auth_token": None,
    },
}


def load_from_disk(filepath):
    global store
    with open(filepath, "r") as f:
        store = json.loads(f.read())


# Load the config into store
load_from_disk(os.path.abspath(os.environ[POLITI_HACK_CONFIG_PATH]))
