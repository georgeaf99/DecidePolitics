import boto.dynamodb2.table as dynamo_table
import boto.dynamodb2.exceptions as dynamo_exceptions
import copy

import jsonpickle

import json
import time
import uuid

import shared.common as common
import shared.config as config
import shared.service as service
import shared.version as version

from shared.common import Errors, PolitiHackException


##############################
# Global vars, consts, extra #
##############################

# Class of table names
table_prefix = config.store["dynamodb"]["table_prefix"]
class TableNames():
    CUSTOMERS = table_prefix + "PolitiHack_Customers"
    VOTES     = table_prefix + "PolitiHack_Votes"

# Tables
customers = dynamo_table.Table(TableNames.CUSTOMERS, connection=service.dynamodb)
votes     = dynamo_table.Table(TableNames.VOTES,     connection=service.dynamodb)

# Use boolean for the tables
customers.use_boolean()
votes.use_boolean()


# Base class for all object models
class Model():
    def __init__(self, item):
        if not self._atts_are_valid(item._data):
            raise PolitiHackException(Errors.INVALID_DATA_PRESENT)

        self.item = item
        self.HANDLERS.migrate_forward_item(item)

    # Factory methods
    @staticmethod
    def load_from_db(cls, key, consistent=True):
        if not issubclass(cls, Model):
            raise ValueError("Class must be a subclass of Model")

        # None keys cause dynamodb exception
        if key is None:
            return None

        item = None
        try:
            full_key = { }
            if ("RANGE_KEY" in cls.__dict__) != (key.find("-") != -1):
                raise PolitiHackException(Errors.DATA_NOT_PRESENT)
            if key.find("-") == -1:
                full_key[cls.KEY] = key
            else:
                split = key.split("-", 2)
                full_key[cls.KEY] = split[0]
                full_key[cls.RANGE_KEY] = int(split[1])

            item = cls(cls.TABLE.get_item(consistent=consistent, **full_key))

            # Migrate the item forward if it is on an old version
            if item["version"] <= cls.VERSION:
                cls.HANDLERS.migrate_forward_item(item)
                if not item.save():
                    return None
        except dynamo_exceptions.ItemNotFound:
            raise PolitiHackException(cls.ITEM_NOT_FOUND_EX)

        return item

    @staticmethod
    def load_from_data(cls, data):
        if not issubclass(cls, Model):
            raise ValueError("Class must be a subclass of Model")

        return cls(dynamo_table.Item(cls.TABLE, data))

    # Attribute access
    def __getitem__(self, key):
        return self.item[key]

    def get(self, key, default=None):
        return self.item[key] if key in self.item else default

    def __setitem__(self, key, val):
        if key in self.VALID_KEYS:
            self.item[key] = val
        else:
            raise ValueError("Attribute %s is not valid." % key)

    def __contains__(self, key):
        return key in self.item

    def update(self, atts):
        for key, val in atts.items():
            self[key] = val

    def _atts_are_valid(self, attributes):
        # Verify that the attributes passed in were valid
        for atr in attributes:
            if atr not in self.VALID_KEYS:
                return False

        return True

    def get_data(self, version=None):
        # Default to the latest version
        new_version = version if version is not None else self.VERSION

        self.HANDLERS.migrate_backward_item(self.item, new_version)
        data = copy.deepcopy(self.item._data)
        self.HANDLERS.migrate_forward_item(self.item)

        return data

    # Database Logic
    def save(self):
        # Defauult dynamodb behavior returns false if no save was performed
        if not self.item.needs_save():
            return True
        # Don't allow empty keys to be saved
        elif any([val == "" for val in self.get_data().values()]):
            raise PolitiHackException(Errors.INVALID_DATA_PRESENT)

        try:
            return self.item.partial_save()
        except dynamo_exceptions.ConditionalCheckFailedException:
            return False

    def create(self):
        # Don't allow empty keys to be saved
        if any([val == "" for val in self.get_data().values()]):
            raise PolitiHackException(Errors.INVALID_DATA_PRESENT)

        if self.is_valid():
            return self.item.save()
        else:
            return False

    def delete(self):
        return self.item.delete()


class CFields():
    UUID = "uuid"
    VERSION = "version"
    PHONE_NUMBER = "phone_number"
    EMAIL = "email"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    ZIP_CODE = "zip_code"


class Customer(Model):
    FIELDS = CFields
    VALID_KEYS = set([getattr(CFields, attr) for attr in vars(CFields)
        if not attr.startswith("__")])
    TABLE_NAME = TableNames.CUSTOMERS
    TABLE = customers
    KEY = CFields.UUID
    MANDATORY_KEYS = set([CFields.VERSION, CFields.PHONE_NUMBER])
    VERSION = 1
    ITEM_NOT_FOUND_EX = Errors.CUSTOMER_DOES_NOT_EXIST

    # Initialize the migration handlers
    HANDLERS = version.MigrationHandlers(VERSION)

    def __init__(self, item):
        super().__init__(item)

    @staticmethod
    def create_new(attributes={}):
        # Default Values
        attributes[CFields.UUID] = common.get_uuid()
        attributes[CFields.VERSION] = Customer.VERSION

        return Model.load_from_data(Customer, attributes)

    def is_valid(self):
        if not self.MANDATORY_KEYS <= set(self.get_data()):
            return False

        # Check to that there is only one customer with this phone_number
        return customers.query_count(
            index="{0}-index".format(self[CFields.PHONE_NUMBER]),
            phone_number__eq=self[CFields.PHONE_NUMBER]) == 0


class VFields():
    CUSTOMER_UUID = "customer_uuid"
    VERSION = "version"
    BILL_ID = "bill_id"
    VOTE_RESULT = "vote_result"


class Votes(Model):
    FIELDS = VFields
    VALID_KEYS = set([getattr(VFields, attr) for attr in vars(VFields)
        if not attr.startswith("__")])
    TABLE_NAME = TableNames.VOTES
    TABLE = votes
    KEY = VFields.CUSTOMER_UUID
    RANGE_KEY = VFields.BILL_ID
    MANDATORY_KEYS = set([VFields.CUSTOMER_UUID, VFields.BILL_ID, VFields.VOTE_RESULT])
    VERSION = 1
    ITEM_NOT_FOUND_EX = Errors.VOTES_DOES_NOT_EXIST

    # Initialize the migration handlers
    HANDLERS = version.MigrationHandlers(VERSION)

    def __init__(self, item):
        super().__init__(item)

    @staticmethod
    def create_new(attributes={}):
        # Default Values
        attributes[VFields.CUSTOMER_UUID] = common.get_uuid()
        attributes[VFields.VERSION] = Votes.VERSION

        return Model.load_from_data(Votes, attributes)

    def is_valid(self):
        if not self.MANDATORY_KEYS <= set(self.get_data()):
            return False

        return True
