from politi_hack.flask import app

from flask import json
from flask import request


@app.route('/')
def health_check():
    return json.jsonify(dict(healthy=True))
