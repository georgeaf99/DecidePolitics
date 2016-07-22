import json
import logging
import os
import requests

import boto.dynamodb2
from boto.dynamodb2.layer1 import DynamoDBConnection
from twilio.rest import TwilioRestClient

import shared.config as config

# Global services. Initalized at bottom
sms = None
shorturl = None
dynamodb = None

#######################
# Service Definitions #
#######################

class SmsService(object):
    def is_connected(self):
        return True

    def send_msg(self, to, body, _from=config.SERVICE_PHONE_NUMBER):
        logging.info("TEST: Sent SMS to {} from {} with body: {}".format(to, _from, body))


class TwilioService(SmsService):
    def __init__(self, account_sid, auth_token):
        self.twilio = TwilioRestClient(account_sid, auth_token)

    def is_connected(self):
        return len(self.twilio.accounts.list()) > 0

    def send_msg(self, to, body, from_=config.SERVICE_PHONE_NUMBER):
        sms_chunks = [body[i : i + config.MAX_TWILIO_MSG_SIZE]
                for i in range(0, len(body), config.MAX_TWILIO_MSG_SIZE)];

        for msg in sms_chunks:
            self.twilio.messages.create(body=msg, to=to, from_=from_)


class ShortUrlService(object):
    def shorten_url(self, long_url):
        logging.info("TEST: shortened url {}".format(long_url))
        return long_url


class GoogleUrlService(object):
    def __init__(self, key):
        self.api_url = 'https://www.googleapis.com/urlshortener/v1/url?key={}'.format(key)

    def shorten_url(self, long_url):
        data = json.dumps(dict(longUrl=long_url))
        headers = {'Content-Type': 'application/json'}

        try:
            resp = requests.post(self.api_url, data=data, headers=headers, timeout=2.0)
        except requests.exceptions.RequestException as e:
            logging.exception(e)
        else:
            if resp.status_code == 200:
                return resp.json()["id"]
            else:
                logging.warning("Received bad status code from google api: %s\n\n%s",
                        resp.status_code, resp.text)
        return long_url


##########################
# Service Initialization #
##########################

def _create_sms():
    cnfg = config.store["twilio"]
    if not cnfg["is_testing"]:
        return TwilioService(cnfg["account_sid"], cnfg["auth_token"])
    else:
        return SmsService()


def _create_dynamodb():
    cnfg = config.store["dynamodb"]
    if not cnfg["is_testing"]:
        logging.info("Connecting to aws dynamodb instance")
        return boto.dynamodb2.connect_to_region(
            cnfg["region"],
            aws_access_key_id=cnfg["access_key"],
            aws_secret_access_key=cnfg["secret_key"],
        )
    else:
        logging.info("Connecting to local dynamodb instance")
        return DynamoDBConnection(
            aws_access_key_id='foo',
            aws_secret_access_key='bar',
            host=cnfg["endpoint"]["hostname"],
            port=cnfg["endpoint"]["port"],
            is_secure=False
        )


def _create_urlshortener():
    cnfg = config.store["google"]
    if cnfg["is_testing"]:
        return ShortUrlService()
    else:
        return GoogleUrlService(cnfg["api_key"])


sms = _create_sms()
dynamodb = _create_dynamodb()
shorturl = _create_urlshortener()
