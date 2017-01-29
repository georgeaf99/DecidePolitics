from decide_politics.transactions import transaction_base as tb

enter_sn = tb.SendMessageStateNode("enter", "ACK TRANSACTION")
ack_back_sn = tb.SendMessageStateNode("ack_back", "ACK")

enter_sn.register_trigger(
    lambda td: td.MESSAGE == "EXIT",
    None
)
enter_sn.register_trigger(
    lambda td: td.MESSAGE == "ACK",
    ack_back_sn
)

ack_back_sn.register_trigger(
    lambda td: td.MESSAGE == "EXIT",
    None
)
ack_back_sn.register_trigger(
    lambda td: td.MESSAGE == "ACK",
    ack_back_sn
)


class AckBackTransaction(tb.TransactionBase):
    ID = "AckBackTransaction"

    STATE_NODES = {
        "enter": enter_sn,
        "ack_back": ack_back_sn
    }

    def __init__(self):
        super().__init__(enter_sn)
