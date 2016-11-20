from decide_politics.transactions import transaction_base as tb

WELCOME_MESSAGE = "Welcome to DecidePolitics!"

welcome_state_node = tb.SendMessageStateNode("welcome", WELCOME_MESSAGE)
# Always exit state upon transitioning
welcome_state_node.register_trigger(
    lambda td: True,
    None
)

class WelcomeTransaction(tb.TransactionBase):
    ID = "WelcomeTransaction"

    def __init__(self):
        super().__init__(welcome_state_node)
