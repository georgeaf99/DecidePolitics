import uuid
from collections import defaultdict

import shared.service as service
import decide_politics.core.models.CFields as CFields
import decide_politics.core.models.CFields as Customer


class TransactionBase:
    def __init__(self, begin_state_node):
        self.ID = str(uuid.uuid4())

        self._cur_state_node = begin_state_node

    def get_transaction_name(self):
        """Returns the name of the transaction

        NOTE that this assumes that all transaction classes will have different names
        """
        return self.__class__.__name__

    def start_transaction(self, customer, message_content):
        """Transition the customer into this transaction"""
        customer[CFields.CUR_TRANSACTION_ID] = self.ID
        customer[CFields.TRANSACTION_STATE_ID] = self._cur_state_node.ID

        self.upon_entering_transaction(customer, message_content)

    def upon_entering_transaction(self, customer, message_content):
        """Determines the logic a customer entering this transaction

        NOTE that default behavior is to pass"""
        pass

    def handle_message(self, customer, message_content):
        self._cur_state_node = self._cur_state_node.handle_message(customer, message_content)

        if self._cur_state_node is None:
            self.exit_transaction(customer, message_content)

    def exit_transaction(self, customer, message_content):
        customer[CFields.CUR_TRANSACTION_ID] = Customer.CUR_TRANSACTION_ID_SENTINEL
        customer[CFields.TRANSACTION_STATE_ID] = Customer.CUR_TRANSACTION_ID_SENTINEL

        self.upon_exiting_transaction(customer, message_content)

    def upon_exiting_transaction(self, customer, message_content):
        pass


class StateNode:
    """A class which manages the logic with traversing a finite state machine (FSM) representing
    the state of a conversation

    Example of Configuration:
        upon_hello = lambda mc: mc == 'HELLO'
        begin_state = StateNode("Welcome to the transaction")
        ack_state = StateNode("")
    """
    def __init__(self, message_to_send):
        """Initialize state node with the message we are going to send to the user"""
        self.ID = str(uuid.uuid4())

        self._message_to_send = message_to_send

        self._trigger_map = []

    def enter(self, customer, message_content):
        """Called when a given customer is transitioning to this state"""
        service.twilio.send_msg(
            customer[CFields.PHONE_NUMBER],
            self._message_to_send,
        )

        self.upon_entering_state(customer, message_content)

    def upon_entering_state(self, customer, message_content):
        """Defines the behavior upon entering this state"""
        raise NotImplementedError()

    def register_trigger(self, trigger_unary_predicate, target_state_node):
        """Register a trigger function which accepts the message content and a target state node

        @param trigger_unary_predicate A function with signature (message_content) -> `bool`
        @param target_state_node The next state node to transition to"""
        self._trigger_map[trigger_unary_predicate] = target_state_node;

    def handle_message(self, customer, message_content):
        """Handles a message by calling all the registered trigger functions. If the trigger returns
        true, enter the target state and return the new state node.

        NOTE that when a new state node is not found, returns None.

        @param message_content The content of the message being handled
        @returns The new state node or None"""
        # Scan for triggers that are valid
        valid_triggers = [trigger_up
            for trigger_up in self._trigger_map
            if trigger_up(message_content)
        ]

        # Handle case where state transition isn't clean
        if len(valid_triggers) > 1:
            raise Exception("State transition was invalid. {trigger_information}".format(dict(
                trigger_information="More than one ({num_target_states}) target states were found.".format(
                        num_target_states=len(valid_triggers)
                    )
            )))
        elif len(valid_triggers) == 0:
            # In this case we should just return none to signify that we are done
            return None

        # Call the handler for this trigger
        next_state_node = valid_triggers[valid_triggers[0]]
        next_state_node.enter(customer, message_content)

        return next_state_node
