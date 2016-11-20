import decide_politics_base_test

import pytest
from unittest.mock import patch

import shared.config as config
import shared.service as service

from decide_politics.core.models import CFields
from decide_politics.core.models import Customer
from decide_politics.transactions import transaction_base as tb
from decide_politics.transactions import welcome

@pytest.fixture
def dummy_customer():
    return Customer.create_new(attributes={
        # Test number not connected to someones real phone
        CFields.PHONE_NUMBER: "+15419670010"
    })

class PatchTwillioService:
    sent_messages = []

    def is_connected(self):
        return True

    def send_msg(self, to, body, _from=config.SERVICE_PHONE_NUMBER):
        self.sent_messages.append((to, body))


@patch('shared.service.twilio', PatchTwillioService())
class TestWelcomeTransaction:
    def test_basic(self, dummy_customer):
        welcome_transaction = welcome.WelcomeTransaction()
        welcome_transaction.start_transaction(dummy_customer)

        assert PatchTwillioService.sent_messages[-1][1] == welcome.WELCOME_MESSAGE
        assert dummy_customer[CFields.CUR_TRANSACTION_ID] == Customer.CUR_TRANSACTION_ID_SENTINEL
        assert dummy_customer[CFields.TRANSACTION_STATE_ID] == Customer.TRANSACTION_STATE_ID_SENTINEL
