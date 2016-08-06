from gator.core.models import CFields
import shared.common as common

def on_message_recieve(customer, message_body):
    """Handler for all recieved SMS messages

    :param `gator.core.models.Customer` Customer: The customer who sent the message
    :param str message_body: The text content of the message
    """
    if message_body == "TEST":
        common.twilio.send_msg(
            customer[CFields.phone_number],
            "WELCOME TO POLITIHACK!",
        )
