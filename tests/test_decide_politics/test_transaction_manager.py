import decide_politics_base_test

import pytest
from unittest.mock import patch

from decide_politics.core.models import CFields
from decide_politics.core.models import Customer
from decide_politics.transactions import transaction_base as tb
from decide_politics.transactions.transaction_manager import TransactionManager

@pytest.fixture
def dummy_customer():
    return Customer.create_new(attributes={
        # Test number not connected to someones real phone
        CFields.PHONE_NUMBER: "+15419670010"
    })

@pytest.fixture
def dummy_transaction():
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

    return DummyTransactionBase()


class TestTransactionManager:
    @patch('decide_politics.transactions.transaction_manager.TransactionManager.COMMAND_TO_TRANSACTION_MAP',
        dict(DUMMY=dummy_transaction()))
    @patch('decide_politics.transactions.transaction_manager.TransactionManager.TRANSACTION_ID_TO_TRANSACTION_MAP',
        {dummy_transaction().ID: dummy_transaction()})
    def test_general(self, dummy_customer, dummy_transaction):
        TransactionManager.handle_message(dummy_customer, "DUMMY")

        assert dummy_customer[CFields.CUR_TRANSACTION_ID] == dummy_transaction.ID
        assert dummy_customer[CFields.TRANSACTION_STATE_ID] == "begin"

        TransactionManager.handle_message(dummy_customer, "TRIGGER TEXT MESSAGE")

        assert dummy_customer[CFields.CUR_TRANSACTION_ID] == dummy_transaction.ID
        assert dummy_customer[CFields.TRANSACTION_STATE_ID] == "end"
