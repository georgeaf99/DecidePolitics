import uuid

import shared.service as service
from decide_politics.core.models import CFields
from decide_politics.core.models import Customer


class TriggerData:
    """Data passed into state node upon entering entering and exiting"""
    def __init__(self, message=None):
        self.MESSAGE = message

class TransactionBase:
    """Base class for transactions that manages transitioning to new state nodes"""

    ID = 'TransactionBase'

    def __init__(self, begin_state_node):
        self.begin_state_node = begin_state_node

    def __advance_to_next_state(self, customer, trigger_data=TriggerData(), exit_on_failure=True):
        cur_state_node = self.STATE_NODES[customer[CFields.TRANSACTION_STATE_ID]]
        is_success, new_state_node = cur_state_node.handle_trigger_event(customer, trigger_data)

        # Handle case where transition failed
        if not is_success:
            if exit_on_failure:
                # Update the state of the transaction and exit
                self.exit_transaction(customer, trigger_data)

            return
        # Handle the case where the transition was from a leaf node
        elif is_success and new_state_node is None:
            self.exit_transaction(customer, trigger_data)
            return

        # Execute the state transition
        customer[CFields.TRANSACTION_STATE_ID] = new_state_node.ID
        new_state_node.enter(customer, trigger_data)

    def get_transaction_name(self):
        """Returns the name of the transaction

        NOTE that this assumes that all transaction classes will have different names
        """
        return self.__class__.__name__

    def start_transaction(self, customer):
        """Transition the customer into this transaction"""
        customer[CFields.CUR_TRANSACTION_ID] = self.ID
        customer[CFields.TRANSACTION_STATE_ID] = self.begin_state_node.ID

        # Call the handler for entering the first state
        self.begin_state_node.enter(customer)

        # Advance to the next state if possible
        self.__advance_to_next_state(
            customer,
            TriggerData(),
            exit_on_failure=False
        )

        self.upon_entering_transaction(customer)

    def upon_entering_transaction(self, customer):
        """Determines the logic for a customer entering this transaction"""
        pass

    def handle_trigger_event(self, customer, trigger_data):
        """Handles a new trigger event for the given customer"""
        self.__advance_to_next_state(customer, trigger_data, exit_on_failure=True)

    def exit_transaction(self, customer, trigger_data=None):
        """Handles class logic for exiting the transaction"""
        customer[CFields.CUR_TRANSACTION_ID] = Customer.CUR_TRANSACTION_ID_SENTINEL
        customer[CFields.TRANSACTION_STATE_ID] = Customer.TRANSACTION_STATE_ID_SENTINEL

        self.upon_exiting_transaction(customer, trigger_data)

    def upon_exiting_transaction(self, customer, trigger_data=None):
        """Determines the logic for a customer exiting this transaction

        NOTE that the default behavior is to pass"""
        pass


class StateNode:
    """A class which manages the logic with traversing a finite state machine (FSM) representing
    the state of a conversation

    Example of Configuration:
        upon_hello = lambda mc: mc == 'HELLO'
        begin_state = StateNode("Welcome to the transaction")
        end_state   = StateNode("Goodbye!")
        begin_state.register_trigger(upon_hello, end_state)

        begin_state.handle_message("HELLO") -> end_state
    """
    def __init__(self, node_id):
        """Initialize state node with the message we are going to send to the user"""
        self.ID = node_id

        self._trigger_map = {}

    def enter(self, customer, trigger_data=TriggerData()):
        """Called when a given customer is transitioning to this state"""
        self.upon_entering_state(customer, trigger_data)

    def upon_entering_state(self, customer, trigger_data):
        """Defines the behavior upon entering this state

        Default behavior is to pass"""
        pass

    def register_trigger(self, trigger_unary_predicate, target_state_node):
        """Register a trigger function which accepts the message content and a target state node

        @param trigger_unary_predicate A function with signature (message_content) -> `bool`
        @param target_state_node The next state node to transition to
        """
        self._trigger_map[trigger_unary_predicate] = target_state_node;

    def handle_trigger_event(self, customer, trigger_data):
        """Handles a message by calling all the registered trigger functions. If the trigger returns
        true, enter the target state and return the new state node.

        NOTE that when a new state node is not found, returns None.

        @param message_content The content of the message being handled
        @param trigger_data The `TriggerData` object containing necessary information
        @returns (Success flag, The new state node or None)
        """
        # Scan for triggers that are valid
        valid_triggers = [trigger_up
            for trigger_up in self._trigger_map
            if trigger_up(trigger_data)
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
            return (False, None)

        # Call the handler for this trigger
        next_state_node = self._trigger_map[valid_triggers[0]]

        return (True, next_state_node)


class SendMessageStateNode(StateNode):
    """State node which sends a message upon entering"""
    def __init__(self, node_id, message_to_send):
        self._message_to_send = message_to_send

        super().__init__(node_id)

    def upon_entering_state(self, customer, trigger_data):
        service.twilio.send_msg(
            customer[CFields.PHONE_NUMBER],
            self._message_to_send,
        )
