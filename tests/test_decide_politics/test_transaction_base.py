import decide_politics_base_test

import pytest

from decide_politics.core.models import CFields
from decide_politics.core.models import Customer
from decide_politics.transactions import transaction_base as tb

@pytest.fixture
def dummy_customer():
    return Customer.create_new(attributes={
        # Test number not connected to someones real phone
        CFields.PHONE_NUMBER: "+15419670010"
    })

class TestStateNode:

    class TestStateNode(tb.StateNode):
        """Subclass used to test StateNode class"""
        def __init__(self, message_to_send):
            super.__init__(message_to_send)

        def upon_entering_state(self, customer, message_content):
            pass

    def test_enter_state(self, dummy_customer):
        BEGIN_MSG = "begin"
        END_MSG = "end"

        test_state_node_begin = TestStateNode(BEGIN_MSG)
        test_state_node_end = TestStateNode(END_MSG)

        TRIGGER_MESSAGE = "TRIGGER TEXT MESSAGE"
        begin_to_end_trigger = lambda msg: msg == TRIGGER_MESSAGE
        test_state_node_begin.register_trigger(
            begin_to_end_trigger,
            test_state_node_end,
        )

        cur_node = test_state_node_begin.handle_message(
            dummy_customer,
            TRIGGER_MESSAGE,
        )

        assert cur_node == test_state_node_end
