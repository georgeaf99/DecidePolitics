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

class DummyStateNode(tb.StateNode):
    """Subclass used to test StateNode class"""
    def __init__(self, message_to_send):
        super().__init__(message_to_send)

    def upon_entering_state(self, customer, message_content):
        pass


class TestStateNode:
    def test_enter_state(self, dummy_customer):
        BEGIN_MSG = "begin"
        END_MSG = "end"

        dummy_state_node_begin = DummyStateNode(BEGIN_MSG)
        dummy_state_node_end = DummyStateNode(END_MSG)

        TRIGGER_MESSAGE = "TRIGGER TEXT MESSAGE"
        begin_to_end_trigger = lambda msg: msg == TRIGGER_MESSAGE
        dummy_state_node_begin.register_trigger(
            begin_to_end_trigger,
            dummy_state_node_end,
        )

        cur_node = dummy_state_node_begin.handle_message(
            dummy_customer,
            TRIGGER_MESSAGE,
        )

        assert cur_node == dummy_state_node_end
        assert cur_node != dummy_state_node_begin
