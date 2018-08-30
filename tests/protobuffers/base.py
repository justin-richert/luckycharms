"""Contains the base protocol buffer transformers."""

import copy
import json

from google.protobuf.json_format import MessageToJson, Parse


class BaseResource(object):
    """Base class for resource transformers."""

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


class BaseCollection(object):
    """Base class for collection transformers."""

    @classmethod
    def dict_to_message(cls, data):
        """Convert a dictionary to a protocol buffer message."""
        message = cls._get_message()
        cls._dict_to_message(data, message)
        if data.get('page_size'):  # pragma: no branch
            message.page_size = data['page_size']
        if data.get('next_page'):
            message.next_page = data['next_page']
        return message

    @classmethod
    def message_to_dict(cls, message):
        """Convert a protocol buffer message to a dictionary."""
        data = {}
        data['data'] = cls._message_to_dict(message)
        if hasattr(message, 'page_size'):  # pragma: no branch
            data['page_size'] = message.page_size
        if hasattr(message, 'next_page'):  # pragma: no branch
            data['next_page'] = message.next_page
        return data

    @classmethod
    def proto_to_dict(cls, proto):
        """Convert a serialized protocol buffer string to a dictionary."""
        message = cls._get_message()
        message.ParseFromString(proto)
        return cls.message_to_dict(message)
