import models.bill as bill
from sunlight import congress

def get_recent_bills():
    bills_list = congress.bills()

    return [ bill.Bill(bill_json) for bill_json in bills_list ]
