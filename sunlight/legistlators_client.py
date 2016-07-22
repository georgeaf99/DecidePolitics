import requests

BASE_PATH="https://openstates.org/api/v1/legislators/"
API_KEY='fabd1be914a141efbc8607435d2a18c0'

"""
Requests a legistlator based on their first name and last name
"""
def get_legistlator(firstname, lastname):
    params = [ ("first_name", firstname), ("last_name", lastname), ("apikey", API_KEY) ]
    r = requests.get(BASE_PATH, dict(params))
    return r.json() if r and r.json() else False
