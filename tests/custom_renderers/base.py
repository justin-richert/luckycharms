"""Contains the base protocol buffer transformers."""

import copy
import json

from flask import request
from flask_exceptions import BadRequest
from google.protobuf.json_format import MessageToJson, Parse
from google.protobuf.message import DecodeError


class BaseResource:
    """Base class for resource transformers."""

    @classmethod
    def loads(cls, val, *args, **kwargs):
        """Do initial load in of data from request depending on content type header."""
        if request.headers['Content-Type'].startswith('application/json'):
            try:
                val = json.loads(val) if val else {}
            except json.JSONDecodeError:
                raise BadRequest(message='Invalid json data')
        elif request.headers['Content-Type'].startswith('application/octet-stream'):
            try:
                val = cls.proto_to_dict(val)
            except DecodeError:
                raise BadRequest(message='Invalid protocol buffer data')
        return val

    @classmethod
    def dumps(cls, val, *args, **kwargs):
        if val:
            if request.headers['Accepts'].startswith('application/json'):
                val = json.dumps(val)
            elif request.headers['Accepts'].startswith('application/octet-stream'):
                val = cls.dict_to_message(val).SerializeToString()
        return val

    @staticmethod
    def _get_message():
        raise NotImplementedError(
            '<custom_renderers.base.Base> may not be directly used to [de]serialize data'
        )

    @classmethod
    def dict_to_message(cls, data):
        """Convert a dictionary to a protocol buffer message."""
        updated_data = copy.deepcopy(data)

        update_data = getattr(cls, '_dict_to_message', None)
        if callable(update_data):
            updated_data = cls._dict_to_message(updated_data)

        text = json.dumps(updated_data)
        return Parse(text, cls._get_message())

    @classmethod
    def message_to_dict(cls, message):
        """Convert a protocol buffer message to a dictionary."""
        data = json.loads(MessageToJson(message, preserving_proto_field_name=True))

        # Some data may need to be manually transformed
        updated_data = getattr(cls, '_message_to_dict', None)
        if callable(updated_data):
            updates = updated_data(message)  # pylint: disable=not-callable
            nested_keys = []
            for key in updates.keys():
                if '.' in key:
                    nested_keys.append(key)
            for key in nested_keys:
                value = updates.pop(key)
                reference = data
                key_pieces = key.split('.')
                for idx, key_piece in enumerate(key_pieces):  # pragma: no branch
                    reference = reference[key_piece]
                    if idx == len(key_pieces) - 2:  # pragma: no branch
                        reference[key_pieces[idx+1]] = value
                        break
            data.update(updates)

        return data

    @classmethod
    def proto_to_dict(cls, proto):
        """Convert a serialized protocol buffer string to a dictionary."""
        message = cls._get_message()
        message.ParseFromString(proto)
        return cls.message_to_dict(message)
