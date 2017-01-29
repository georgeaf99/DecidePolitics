from decide_politics.core.models import CFields
from decide_politics.transactions.transaction_manager import TransactionManager
import shared.service as service

def on_message_recieve(customer, message_body):
    """Handler for all recieved SMS messages

    @param Customer The customer who sent the message
    @param message_body The text content of the message
    """
    if message_body == "TEST":
        service.twilio.send_msg(
            customer[CFields.PHONE_NUMBER],
            "WELCOME TO DECIDE POLITICS!",
        )

    TransactionManager.handle_message(customer, message_body)
