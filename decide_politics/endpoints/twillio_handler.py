from decide_politics.flask import app

from flask import request
import jsonpickle

from decide_politics.core.models import CFields
from decide_politics.core.models import Customer
import decide_politics.logic.messaging as messaging
import decide_politics.logic.customer_lifecycle as customer_lc


@app.route('/sms/handle_sms', methods=["POST"])
def handle_sms():
    """Handles Twillio SMS message"""
    customer_phone_number = request.values["From"]
    text_message_body = request.values["Body"]

    # Retrieve the customer from the DB or create a new one
    customer = Customer.get_customer_by_phone_number(customer_phone_number)
    if not customer:
        # Save the customer to the DB
        customer = Customer.create_new({
            CFields.PHONE_NUMBER: customer_phone_number,
        })
        customer.create()

        customer_lc.on_new_customer()

    messaging.on_message_recieve(customer, text_message_body)

    return jsonpickle.encode(dict(
        success=True
    ))
