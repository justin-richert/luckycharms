"""
Provide transformers for test.

Named "proto.py" to avoid having pytest perceive this as a test file.
"""

from . import base, proto_pb2


class Test(base.BaseResource):
    """Settings resource protocol buffer transformer."""

    @staticmethod
    def _get_message():
        """Determines the message to be used during transformation."""

        return proto_pb2.Test()


class TestCollection(base.BaseCollection):
    """Image collection protocol buffer transformer."""

    @staticmethod
    def _get_message():
        """Determines the message to be used during transformation."""

        return proto_pb2.TestCollection()
