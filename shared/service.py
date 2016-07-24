import enum
import json
import logging
import os
import requests

import boto.dynamodb2
from boto.dynamodb2.layer1 import DynamoDBConnection
from twilio.rest import TwilioRestClient

import shared.config as config

log = logging.getLogger(__name__)

# Global services. Initalized at bottom
dynamodb = None
shorturl = None
sunlight = None
twilio = None

#######################
# Service Definitions #
#######################

class MockTwillioService:
    def is_connected(self):
        return True

    def send_msg(self, to, body, _from=config.SERVICE_PHONE_NUMBER):
        log.info("TEST: Sent SMS to {} from {} with body: {}".format(to, _from, body))


class TwilioService:
    def __init__(self, account_sid, auth_token):
        self.twilio = TwilioRestClient(account_sid, auth_token)

    def is_connected(self):
        return len(self.twilio.accounts.list()) > 0

    def send_msg(self, to, body, from_=config.SERVICE_PHONE_NUMBER):
        sms_chunks = [body[i : i + config.MAX_TWILIO_MSG_SIZE]
                for i in range(0, len(body), config.MAX_TWILIO_MSG_SIZE)];

        for msg in sms_chunks:
            self.twilio.messages.create(body=msg, to=to, from_=from_)


class SunlightFoundationService:
    """Creates a hybrid service for interacting with both the sunlight REST API and python client"""

    TIMEOUT = 5

    class SunlightAPIs(enum.Enum):
        # Map to the base URL of the API
        CONGRESS = 'congress.api.sunlightfoundation.com'
        OPEN_STATES = 'openstates.org'

    def __init__(self, api_key):
        self.api_key = api_key
        import sunlight
        self.sunlight_python_client = sunlight

        # Set up python client with API key
        self.sunlight_python_client.config.API_KEY = self.api_key

    def send_api_request(self, api, method, path, data={}, version=None, **kwargs):
        """Send an request to the Sunlight REST API

        :param api: The sunlight API to use
        :type api: `SunlightFoundationService.SunlightAPIs`
        :param str method: The REST method to use for this request
        :param str path: The path to append to the API
        :param dict data: The data to be sent as JSON with the request
        :param int version: The version of this API
        :param kwargs: Optional query parameters

        NOTE that if path doesn't have a leading / one will added

        :returns: (status, )
        :rtype: (int, )
        """
        # Normalizing path
        path = "/{path}/".format(path=path.strip('/'))

        # Update the query params w/ the right key
        if api == self.SunlightAPIs.CONGRESS:
            kwargs.update(dict(apikey=self.api_key))
        elif api == self.SunlightAPIs.OPEN_STATES:
            kwargs.update(dict(key=self.api_key))

        url = self._create_url(api, path, version=version)

        method_to_request_funcs = dict(
            GET=requests.get,
            PUT=requests.put,
            POST=requests.post,
        )

        # Choose a method and send the request
        http_method_request_func = method_to_request_funcs[method]
        resp = http_method_request_func(
            url=url,
            params=kwargs,
            data=data,
            timeout=self.TIMEOUT
        )

    def _create_url(self, api, path, version=None):
        """Create the URL for an API request"""
        return "https://{api_base_url}/api{version}{path}".format(
            api_base_url=api.value,
            version=("" if not version else ("/v%s" % version)),
            path=path
        )


class MockGoogleShortenUrlService(object):
    def shorten_url(self, long_url):
        log.info("TEST: shortened url {}".format(long_url))
        return long_url


class GoogleShortenUrlService(object):
    def __init__(self, key):
        self.api_url = 'https://www.googleapis.com/urlshortener/v1/url?key={key}'.format(key=key)

    def shorten_url(self, long_url):
        data = json.dumps(dict(longUrl=long_url))
        headers = {'Content-Type': 'application/json'}

        try:
            resp = requests.post(
                self.api_url,
                data=data,
                headers=headers,
                timeout=2.0
            )
        except requests.exceptions.RequestException:
            log.exception("Google URL shortener encountered an unexpected exception")
        else:
            if resp.status_code == 200:
                return resp.json()["id"]
            else:
                logging.error(
                    "Received bad status code from Google API: {status}\n{text}",
                    status=resp.status_code, text=resp.text
                )

        return long_url


##########################
# Service Initialization #
##########################

def _create_dynamodb():
    cnfg = config.store["dynamodb"]
    if not cnfg["is_testing"]:
        log.info("Creating client for AWS dynamodb instance")
        return boto.dynamodb2.connect_to_region(
            cnfg["region"],
            aws_access_key_id=cnfg["access_key"],
            aws_secret_access_key=cnfg["secret_key"],
        )
    else:
        log.info("Creating client for local dynamodb instance")
        return DynamoDBConnection(
            aws_access_key_id='foo',
            aws_secret_access_key='bar',
            host=cnfg["endpoint"]["hostname"],
            port=cnfg["endpoint"]["port"],
            is_secure=False
        )


def _create_sunlight():
    cnfg = config.store["sunlight"]

    log.info("Creating client for Sunlight Foundation API")
    return SunlightFoundationService(cnfg["api_key"])


def _create_urlshortener():
    cnfg = config.store["google"]
    if cnfg["is_testing"]:
        return MockGoogleShortenUrlService()
    else:
        log.info("Creating client for Google url shortener")
        return GoogleShortenUrlService(cnfg["api_key"])


def _create_twilio():
    cnfg = config.store["twilio"]
    if not cnfg["is_testing"]:
        log.info("Creating client for Twilio API")
        return TwilioService(cnfg["account_sid"], cnfg["auth_token"])
    else:
        log.info("Creating client for mock Twillio")
        return MockTwillioService()


# Initialize global services
dynamodb = _create_dynamodb()
shorturl = _create_urlshortener()
sunlight = _create_sunlight()
twilio = _create_twilio()
