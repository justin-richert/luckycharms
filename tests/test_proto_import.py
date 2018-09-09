"""Test the logger extension module."""
# pylint: disable=protected-access,redefined-outer-name,unused-variable,invalid-name
import importlib
import json
import sys

import google
import pytest
from marshmallow import fields

from conftest import app
from luckycharms import base
from protobuffers import proto


def setup_module():
    """Set up tests."""
    # Force luckycharms.base to load without protobuf in the environment
    sys.modules['google'] = None
    sys.modules['google.protobuf'] = None
    sys.modules['google.protobuf.message'] = None
    importlib.reload(base)


def teardown_module():
    """Tear down tests."""
    # pylint: disable=invalid-name
    sys.modules['google'] = google
    sys.modules['google.protobuf'] = google.protobuf
    sys.modules['google.protobuf.message'] = google.protobuf.message
    # Reload luckycharms.base to restore sys.modules to correct state
    importlib.reload(base)


def test_without_proto():

    class TestSchema(base.BaseModelSchema):
        a = fields.Integer()
        b = fields.String()

    @TestSchema()
    def business_logic(*args, **kwargs):
        return {
            'a': 1,
            'b': 'One'
        }

    with app.test_request_context('/'):
        result = business_logic()
        assert json.loads(result) == {
            'a': 1,
            'b': 'One'
        }

    class TestSchema(base.BaseModelSchema):
        a = fields.Integer()
        b = fields.String()

        config = {
            'protobuffers': {
                'load': proto.Test(),
                'dump': proto.Test(),
                'load_many': proto.Test(),
                'dump_many': proto.TestCollection()
            }
        }

    with pytest.raises(Exception) as excinfo:
        @TestSchema()
        def business_logic(*args, **kwargs):
            return {
                'a': 1,
                'b': 'One'
            }

    assert excinfo.exconly() == "Exception: protobuffer libraries not installed; please install " \
        "luckycharms with extra 'proto' (for example, pip install luckycharms[proto])"
