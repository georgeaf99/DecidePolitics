import models.legistlator as legistlator

from sunlight import congress

def get_legistlator(last_name):
    results = congress.legislators(last_name=last_name)

    if results:
        return legistlator.Legistlator(results[0])
    else:
        # TODO: throw exception
        return False
