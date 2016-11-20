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
    def test_enter_state(self, dummy_customer):
        state_node_begin = tb.StateNode("0")
        state_node_end = tb.StateNode("1")

        TRIGGER_MESSAGE = "TRIGGER TEXT MESSAGE"
        begin_to_end_trigger = lambda msg: msg == TRIGGER_MESSAGE
        state_node_begin.register_trigger(
            begin_to_end_trigger,
            state_node_end,
        )

        is_success, new_state_node = state_node_begin.handle_trigger_event(
            dummy_customer,
            TRIGGER_MESSAGE,
        )

        assert new_state_node == state_node_end
        assert new_state_node != state_node_begin
        assert is_success


class TestTransactionBase:

    # Helper class used to test `TransactionBase`
    class DummyTransactionBase(tb.TransactionBase):
        ID = "dummy_id"

        def __init__(self):
            # Set up the state transaction mechanism
            state_node_begin = tb.StateNode("begin")
            state_node_end = tb.StateNode("end")

            TRIGGER_MESSAGE = "TRIGGER TEXT MESSAGE"
            begin_to_end_trigger = lambda trigger_data: trigger_data.MESSAGE == TRIGGER_MESSAGE
            state_node_begin.register_trigger(
                begin_to_end_trigger,
                state_node_end,
            )

            super().__init__(state_node_begin)

    def test_general(self, dummy_customer):
        dummy_inst = self.DummyTransactionBase()
        dummy_inst.start_transaction(dummy_customer)

        # Correct ininitial state
        assert dummy_inst.get_transaction_name() == "DummyTransactionBase"
        assert dummy_inst.ID == "dummy_id"
        assert dummy_inst._cur_state_node.ID == "begin"
        assert dummy_customer[CFields.CUR_TRANSACTION_ID] == self.DummyTransactionBase.ID
        assert dummy_customer[CFields.TRANSACTION_STATE_ID] == "begin"

        # Transition to a new state
        dummy_inst.handle_message(dummy_customer, "TRIGGER TEXT MESSAGE")

        # Correct final state
        assert dummy_inst.get_transaction_name() == "DummyTransactionBase"
        assert dummy_inst.ID == "dummy_id"
        assert dummy_inst._cur_state_node.ID == "end"
        assert dummy_customer[CFields.CUR_TRANSACTION_ID] == self.DummyTransactionBase.ID
        assert dummy_customer[CFields.TRANSACTION_STATE_ID] == "end"
