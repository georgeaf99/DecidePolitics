import logging
import subprocess

import shared.config as config

log = logging.getLogger(__name__)

# Flask commands to run
FLASK_COMMAND = "python3.5 -m flask run --host={host_name} --port={port}".format(
    host_name=config.store['api_host']['name'],
    port=config.store['api_host']['port'],
)
FLASK_COMMAND_ARGS = FLASK_COMMAND.split(" ")


def start_flask_server():
    log.info("Starting PolitiHack Flask App")

    ret_code = subprocess.call(FLASK_COMMAND_ARGS)

    if ret_code == 0:
        log.info("PolitiHack flask app terminated successfully")
    else:
        log.info("PolitiHack flask app terminated with return code: {ret_code}".format(
            ret_code=ret_code
        ))


if __name__ == "__main__":
    start_flask_server()
