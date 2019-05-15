import datetime
import json
import os

import flask
import flask_exceptions
import pytest
from marshmallow import RAISE, Schema, ValidationError, fields, validates

os.environ['LUCKYCHARMS_SHOW_ERRORS'] = 'true'

from luckycharms.base import (BaseModelSchema,  # isort:skip  # noqa
                              QuerystringCollection, QuerystringResource)


try:
    from protobuffers import proto
except ImportError:
    pass

app = flask.Flask(__name__)
app.app_ctx_globals_class.content_type = 'application/json'


def test_no_config():
    """
    Test that a schema can be defined the same way a base marshmallow schema can be defined.
    No configuration is required. Defaults to paging=False and default querystring functionality.
    """

    class TestSchema(BaseModelSchema):
        a = fields.Int()

    test_schema = TestSchema()

    assert test_schema.config == {
        'paged': True,
        'querystring_schemas': {
            'load': QuerystringResource,
            'load_many': QuerystringCollection
        }
    }


def test_partial_config():

    class TestSchema(BaseModelSchema):
        a = fields.Int()

        config = {
            'ordering': [
                ('a', ('asc', 'desc'))
            ]
        }
    test_schema = TestSchema()
    assert test_schema.config == {
        'paged': True,
        'querystring_schemas': {
            'load': QuerystringResource,
            'load_many': QuerystringCollection
        },
        'ordering': [
            ('a', ('asc', 'desc'))
        ]
    }

    class TestSchema(BaseModelSchema):
        a = fields.Int()

        config = {
            'querystring_schemas': {
                'load_many': object,
            }
        }
    test_schema = TestSchema()
    assert test_schema.config == {
        'paged': True,
        'querystring_schemas': {
            'load': QuerystringResource,
            'load_many': object
        }
    }

    class TestSchema(BaseModelSchema):
        a = fields.Int()

        config = {
            'querystring_schemas': {
                'load': object,
            },
            'ordering': [
                ('a', ('desc',))
            ]
        }
    test_schema = TestSchema(many=True)
    assert test_schema.config == {
        'paged': True,
        'querystring_schemas': {
            'load': object,
            'load_many': QuerystringCollection
        },
        'ordering': [
            ('a', ('desc',))
        ]
    }


def test_querystring_schemas():

    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()
        c = fields.Boolean()

        config = {
            'ordering': [
                ('a', ('asc',))
            ]
        }

        class Meta:
            load_only = ('b',)
            exclude = ('c',)

    test_schema = TestSchema()
    assert test_schema.many is False
    assert isinstance(test_schema.querystring_schema, QuerystringResource)
    assert test_schema.querystring_schema.allowed_fields == {'a'}

    test_schema = TestSchema(many=True)
    assert test_schema.many is True
    assert isinstance(test_schema.querystring_schema, QuerystringCollection)
    assert test_schema.querystring_schema.allowed_fields == {'a'}


def test_marshmallow_parameters():
    """Show that schemas are still fully functioning marshmallow schemas."""

    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()
        c = fields.Boolean()
        d = fields.Float()

    @TestSchema(
        many=False,
        dump_only=('a',),
        load_only=('b',),
        exclude=('c',),
        prefix='test',
        unknown=RAISE
    )
    def business_logic(*args, **kwargs):
        fake_data = {
            'a': 1,
            'b': 'Message',
            'c': False,
            'd': 1.243958
        }
        fake_data.update(kwargs)
        return fake_data

    # Show that b and c are not returned due to load_only and exclude respectively
    # Returned values are prefixed with "test", honoring "prefix" kwarg
    with app.test_request_context('/'):
        result = business_logic()
        assert json.loads(result) == {
            'testa': 1,
            'testd': 1.243958
        }

    # Show that load only is respected (and because unknown is set to raise an error, this does so)
    with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'a': 2, 'd': 1.01}),
            headers={'Content-Type': 'application/json'}
            ):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == 'a: Unknown field.'

    with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'d': 1.01}),
            headers={'Content-Type': 'application/json'}
            ):
        result = business_logic()
        assert json.loads(result) == {
            'testa': 1,
            'testd': 1.01
        }

    # if json is badly formed this should be a 400
    with app.test_request_context(
            '/',
            method='POST',
            data="{'d': 1000}",  # wrong quotes for an inlined json
            headers={'Content-Type': 'application/json'}
            ):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()


def test_marshmallow_hack():

    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()
        c = fields.Boolean()

    @TestSchema()
    def business_logic(*args, **kwargs):
        # business logic
        return {
            'a': 1,
            'b': 'Message',
            'c': False
        }

    # Test field specifying functionality of default querystring
    with app.test_request_context('/?fields=a,c'):
        data = json.loads(business_logic())
        assert data == {
            'a': 1,
            'c': False
        }

    with app.test_request_context('/?fields=b,c'):
        data = json.loads(business_logic())
        assert data == {
            'b': 'Message',
            'c': False
        }

    # Test invalid field request
    with app.test_request_context('/?fields=a,d'):
        with pytest.raises(flask_exceptions.BadRequest):
            data = json.loads(business_logic())

    data = {'b': 'string value', 'c': True}
    with app.test_request_context(
            '/',
            method='POST',
            data=data,
            headers={'Content-Type': 'application/json'}
            ):
        data = business_logic()


def test_collections():

    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()

        config = {
            'paged': False
        }

    @TestSchema(many=True)
    def business_logic(*args, **kwargs):
        return [
            {
                'a': 1,
                'b': 'One'
            },
            {
                'a': 2,
                'b': 'Two'
            }
        ]

    with app.test_request_context('/'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'a': 1,
                    'b': 'One'
                },
                {
                    'a': 2,
                    'b': 'Two'
                }
            ]
        }

    # Test unordered, paged collection
    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()

    @TestSchema(many=True)
    def business_logic(*args, **kwargs):
        return [
            {
                'a': 1,
                'b': 'One'
            },
            {
                'a': 2,
                'b': 'Two'
            }
        ]

    with app.test_request_context('/'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'a': 1,
                    'b': 'One'
                },
                {
                    'a': 2,
                    'b': 'Two'
                }
            ],
            'next_page': False,
            'page_size': 25
        }

    class TestSchema(BaseModelSchema):
        a = fields.Int(order=('desc',))
        b = fields.String(order=('asc', 'desc'))

    @TestSchema(many=True)
    def business_logic(fields, page, page_size, order, order_by):
        data = [
            {
                'a': 1,
                'b': 'One'
            },
            {
                'a': 2,
                'b': 'Two'
            }
        ]
        return sorted(
            data,
            key=lambda x: x[order_by],
            reverse=True if order == 'desc' else False
        )[(page - 1)*page_size:page*page_size + 1]

    with app.test_request_context('/?page=1&&page_size=1&order_by=a&order=desc'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'a': 2,
                    'b': 'Two'
                },
            ],
            'next_page': True,
            'page_size': 1
        }

    with app.test_request_context('/?page=2&&page_size=1&order_by=a&order=desc'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'a': 1,
                    'b': 'One'
                },
            ],
            'next_page': False,
            'page_size': 1
        }

    with app.test_request_context('/?page=1&order_by=b&order=asc&fields=a'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'a': 1,
                },
                {
                    'a': 2
                }
            ],
            'next_page': False,
            'page_size': 25
        }

    with app.test_request_context('/?page=1&order_by=b&order=desc&fields=b'):
        result = business_logic()
        assert json.loads(result) == {
            'data': [
                {
                    'b': 'Two',
                },
                {
                    'b': 'One'
                }
            ],
            'next_page': False,
            'page_size': 25
        }


def test_paging_validation():
    class TestSchema(BaseModelSchema):
        a = fields.Int(order=('desc',))
        b = fields.String(order=('asc', 'desc'))
        c = fields.Boolean()

    @TestSchema(many=True)
    def business_logic(fields, page, page_size, order, order_by):
        pass  # pragma: no cover

    with app.test_request_context('/?page=51'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == 'page: Not a valid page.'

    with app.test_request_context('/?page=abc'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == 'page: Not a valid page.'

    with app.test_request_context('/?invalid_arg=value'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: invalid_arg is an invalid querystring argument.'

    with app.test_request_context('/?page=*&fields=*'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: Maximum two fields allowed for page=*.'

    with app.test_request_context('/?page=*&fields=a'):
        business_logic()


def test_unconditional_paging_validation():
    """Test the unconditional_paging configuration."""

    class UnconditionalPagingQuerystringCollection(QuerystringCollection):
        """Custom Querystring Collection Schema that allows unconditional paging."""
        config = {'unconditional_paging': True}

    class TestSchema(BaseModelSchema):
        a = fields.Int(order=('desc',))
        b = fields.String(order=('asc', 'desc'))
        c = fields.Boolean()

        config = {
            'querystring_schemas': {
                'load_many': UnconditionalPagingQuerystringCollection,
            }
        }

    @TestSchema(many=True)
    def business_logic(fields, page, page_size, order, order_by):
        pass  # pragma: no cover

    with app.test_request_context('/?page=*&fields=*'):
        business_logic()


def test_ordering_validation():

    class TestSchema(BaseModelSchema):
        a = fields.Int(order=('desc',))
        b = fields.String()

    @TestSchema(many=True)
    def business_logic(fields, page, page_size, order, order_by):
        pass  # pragma: no cover

    with app.test_request_context('/?order_by=b&order=asc'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: Not a valid field to order by.'

    with app.test_request_context('/?order_by=a&order=asc'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: Not a valid order for field.'

    class TestSchema(BaseModelSchema):
        a = fields.Int(order=('sideways',))

    with pytest.raises(Exception) as excinfo:
        @TestSchema(many=True)
        def business_logic(fields, page, page_size, order, order_by):
            pass  # pragma: no cover
    assert str(excinfo.value) == 'Invalid order option "sideways" provided for field a.'

    class TestSchema(BaseModelSchema):
        a = fields.Int()

    @TestSchema(many=True)
    def business_logic(fields, page, page_size, order, order_by):
        pass  # pragma: no cover

    with app.test_request_context('/?order_by=a'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: order_by is an invalid querystring argument.'

    with app.test_request_context('/?order=asc'):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == '_schema: order is an invalid querystring argument.'


def test_nested_field_error_message():

    class NestedSchema(Schema):
        nested_field_1 = fields.Int()
        nested_field_2 = fields.String(required=True)

    class TestSchema(BaseModelSchema):
        a = fields.Nested(NestedSchema)

    @TestSchema()
    def business_logic(*args, **kwargs):
        pass  # pragma: no cover

    with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'a': {'nested_field_1': 1}}),
            headers={'Content-Type': 'application/json'}
            ):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == \
            "a: {'nested_field_2': ['Missing data for required field.']}"


def test_unsupported_media():

    class TestSchema(BaseModelSchema):
        a = fields.Int()

        @validates('a')
        def raise_unsupported_media_error(self, data):
            raise ValidationError('Unsupported Media', error_code=415)

    @TestSchema()
    def business_logic(*args, **kwargs):
        pass  # pragma: no cover

    with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'a': 1}),
            headers={'Content-Type': 'application/json'}
            ):
        with pytest.raises(flask_exceptions.UnsupportedMedia):
            business_logic()


def test_empty_response():

    class TestSchema(BaseModelSchema):
        a = fields.Int()

    @TestSchema()
    def business_logic(*args, **kwargs):
        return

    with app.test_request_context('/'):
        result = business_logic()
        assert result == ''


def test_last_modified_hook():

    class TestModel:

        a = None
        updated_dt = None

    class TestSchema(BaseModelSchema):
        a = fields.Int()

    @TestSchema()
    def business_logic(*args, **kwargs):
        resp = TestModel()
        resp.a = 1
        resp.updated_dt = datetime.datetime.utcnow()
        return resp

    with app.test_request_context('/'):
        result = business_logic()
        assert json.loads(result) == {
            'a': 1
        }


@pytest.mark.parametrize(
    'content_type',
    [{'content_type': 'application/octet-stream'}],
    indirect=True
)
def test_proto_rendering():

    class TestSchema(BaseModelSchema):
        a = fields.Int()
        b = fields.String()
        c = fields.Boolean()

        config = {
            'ordering': [
                ('a', ('asc',))
            ],
            'protobuffers': {
                'load': proto.Test(),
                'dump': proto.Test(),
                'load_many': proto.Test(),
                'dump_many': proto.TestCollection()
            }
        }

    @TestSchema()
    def business_logic(*args, **kwargs):
        return {
            'a': 1,
            'b': 'One',
            'c': True
        }

    with app.test_request_context(
            '/',
            method='POST',
            data=proto.Test().dict_to_message({'a': 2, 'b': 'Two', 'c': False}).SerializeToString(),
            headers={
                'Content-Type': 'application/octet-stream',
                'Accepts': 'application/octet-stream'
            }):
        result = business_logic()
        assert isinstance(result, bytes)
        result = proto.Test().proto_to_dict(result)
        assert result == {
            'a': 1,
            'b': 'One',
            'c': True
        }

    proto_data = proto.Test().dict_to_message({'a': 2, 'b': 'Two', 'c': False}).SerializeToString()
    with app.test_request_context(
            '/',
            method='POST',
            data=proto_data[:-1],
            headers={
                'Content-Type': 'application/octet-stream',
                'Accepts': 'application/octet-stream'
            }):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        assert excinfo.value.message == 'Invalid protocol buffer data'
