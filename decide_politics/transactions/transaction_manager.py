from decide_politics.core.models import CFields
from decide_politics.core.models import Customer

from decide_politics.transactions import transaction_base as tb
from decide_politics.transactions.welcome import WelcomeTransaction

class TransactionManager:
    """Class that handles transaction lifecycles and delegates messages"""
    COMMAND_TO_TRANSACTION_MAP = {
        "WELCOME": WelcomeTransaction()
    }

    TRANSACTION_ID_TO_TRANSACTION_MAP = {
        WelcomeTransaction.ID: COMMAND_TO_TRANSACTION_MAP["WELCOME"]
    }

    @staticmethod
    def __format_message(message):
        message = message.strip()
        message = message.upper()

        return message

    @classmethod
    def handle_message(cls, customer, message):
        message = cls.__format_message(message)
        trigger_data = tb.TriggerData(message=message)

        customer_cur_trans_id = customer[CFields.CUR_TRANSACTION_ID]

        # Handle case where a customer is not in a transaction
        if customer_cur_trans_id is None or customer_cur_trans_id == Customer.CUR_TRANSACTION_ID_SENTINEL:
            cls.COMMAND_TO_TRANSACTION_MAP[message].start_transaction(customer)
        else:
            cls.TRANSACTION_ID_TO_TRANSACTION_MAP[customer_cur_trans_id].handle_trigger_event(
                customer,
                trigger_data
            )

        customer.save()
