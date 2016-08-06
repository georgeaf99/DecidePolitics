from politi_hack.flask import app

from flask import request

from gator.core.models import Customer
from gator.logic.messaging as messaging

@app.route('/sms/handle_sms', methods=["POST"])
def handle_sms():
    """Handles Twillio SMS message"""
    customer_phone_number = request.values["From"]
    text_message_body = request.values["Body"]

    # Retrieve the customer from DB and send it over to event handler
    customer = Customer.load_from_db(customer_phone_number)
    messaging.on_message_recieve(customer, text_message_body)
