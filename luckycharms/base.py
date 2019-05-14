"""Base schema file."""
# pylint: disable=no-self-use
import json
import os

from flask import g, request
from flask_exceptions.extension import BadRequest, UnsupportedMedia
from marshmallow import Schema, ValidationError
from marshmallow import fields as _fields
from marshmallow import (post_dump, post_load, pre_dump, pre_load,
                         validate, validates, validates_schema)

try:
    from google.protobuf.message import DecodeError
    PROTBUF_IMPORTED = True
except ImportError:
    PROTBUF_IMPORTED = False

# Read in environment variables for configuration
_MAX_PAGE_SIZE_ENV_VAR = os.environ.get('LUCKYCHARMS_MAX_PAGE_SIZE')
try:
    MAX_PAGE_SIZE = int(_MAX_PAGE_SIZE_ENV_VAR)
except (ValueError, TypeError):
    MAX_PAGE_SIZE = 25


_MAX_PAGES_ENV_VAR = os.environ.get('LUCKYCHARMS_MAX_PAGES')
try:
    MAX_PAGES = int(_MAX_PAGES_ENV_VAR)
except (ValueError, TypeError):
    MAX_PAGES = 50

_SHOW_ERR_ENV_VAR = os.environ.get('LUCKYCHARMS_SHOW_ERRORS', 'False')
SHOW_ERRORS = _SHOW_ERR_ENV_VAR in ['True', 'true']


class ErrorHandlingSchema(Schema):
    """Base schema class that knows how to handle errors."""
    def handle_error(self, error, data):
        """Overridden method to return 400s."""
        msg = ''
        # v may be a dictionary instead of a list
        if SHOW_ERRORS:
            for key, value in error.messages.items():
                if isinstance(value, dict):
                    val = str(value)
                else:
                    val = ', '.join(value)
                msg += '{}: {};'.format(key, val)
            msg = msg[:-1]

        code = error.kwargs.get('error_code')
        if code == 415:
            raise UnsupportedMedia(message=msg)
        else:
            raise BadRequest(message=msg)


class BaseModelSchema(ErrorHandlingSchema):
    """Base schema for all others to extend."""

    querystring_schema = None

    def __init__(self, *args, **kwargs):
        """Extended init method for BaseModelSchema to initialize with configuration."""
        super(BaseModelSchema, self).__init__(*args, **kwargs)

        default_config = {
            'paged': True,
            'querystring_schemas': {
                'load': QuerystringResource,
                'load_many': QuerystringCollection
            }
        }
        self.config = {**default_config, **getattr(self, 'config', {})}
        if 'load' not in self.config['querystring_schemas']:
            self.config['querystring_schemas']['load'] = QuerystringResource
        if 'load_many' not in self.config['querystring_schemas']:
            self.config['querystring_schemas']['load_many'] = QuerystringCollection

        if self.config.get('protobuffers') and not PROTBUF_IMPORTED:
            raise Exception(
                "protobuffer libraries not installed; please install"
                " luckycharms with extra 'proto' (for example, pip install luckycharms[proto])")

        self.set_querystring_schema(**kwargs)

    def __call__(self, decorated):
        """Make BaseModelSchema callable so it can be used as a decorator."""
        self._decorated = decorated  # pylint: disable=attribute-defined-outside-init
        return self.function_wrapper

    def function_wrapper(self, **kwargs):
        """Wrapper to be returned by __call__ that will wrap all decorated view helpers."""

        # Workaround until marshmallow provides a way to specify fields at serialization time.
        self.context = {}
        # only = None
        self._types_seen = set()
        self.only = None
        # Load with querystring schemas for GET requests
        if request.method == 'GET':
            params = self.querystring_schema.load(request.args.items())

            # Set serialization fields
            if params['fields'] != "*":
                self.only = params['fields'].split(',')

            # Set context for use in serialization method
            if self.many and self.config['paged']:
                self.context.update({
                    'page': params['page'],
                    'page_size': params['page_size']
                })

        # Load with model schemas for POST, PUT requests
        else:
            params = self.load(request.data, many=self.many)

        kwargs.update(params)

        # Call decorated function
        data = self.dump(self._decorated(**kwargs))

        return data

    def set_querystring_schema(self, **kwargs):
        """Configure querystring schema based on Meta options in model schema."""

        # Only use querystring collection schema if request is to a collection
        # and has a paged response (as informed by Meta class on schema)
        # Otherwise use querystring resource schema
        many = kwargs.get('many')
        querystring_schema = None

        if many and self.config['paged']:
            querystring_schema = self.config['querystring_schemas']['load_many']
            # Pass ordering info from Config class on schema
            ordering = []
            for name, field in self.fields.items():
                if field.metadata.get('order'):
                    for entry in field.metadata['order']:
                        if entry not in ('asc', 'desc'):
                            raise Exception(
                                f'Invalid order option "{entry}" provided for field {field.name}.')
                    ordering.append((name, field.metadata['order']))
            self.querystring_schema = querystring_schema(ordering=ordering)
        else:
            querystring_schema = self.config['querystring_schemas']['load']
            self.querystring_schema = querystring_schema()

        self.querystring_schema.allowed_fields = set(self.fields) - \
            set(self.exclude) - set(self.load_only)

    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    @pre_dump(pass_many=True)
    def pre_dump_func(self, data, many):
        """
        Set the last modified value for resources at the global level for use
        in constructing headers later.
        """
        if data and not many and hasattr(data, 'updated_dt'):
            g.last_modified = data.updated_dt or getattr(data, 'created_dt', None)
        return data

    @pre_load(pass_many=True)
    def pre_load_func(self, data, many):  # pylint: disable=unused-argument
        """Do initial load in of data from request depending on content type header."""
        if request.headers['Content-Type'].startswith('application/json'):
            try:
                data = json.loads(data) if data else {}
            except json.JSONDecodeError:
                raise BadRequest(message='Invalid json data')
        elif request.headers['Content-Type'].startswith(  # pragma: no branch
                'application/octet-stream'):
            transformer = self.config['protobuffers']['load_many'] if self.many \
                else self.config['protobuffers']['load']
            try:
                data = transformer.proto_to_dict(data)
            except DecodeError:
                raise BadRequest(message='Invalid protocol buffer data')
        return data

    # pylint: disable=unexpected-keyword-arg,no-value-for-parameter
    @post_dump(pass_many=True)
    def post_dump_func(self, data, many):
        """Format response depending on whether it is a resource or collection."""
        def handle_collections(data):
            """Format response according to whether its a collection or resource request."""
            if data and many:
                if 'page' in self.context:  # pragma: no branch
                    page = self.context['page']
                    page_size = self.context['page_size']
                    data = {
                        'data': data[:page_size if page else None],
                        'page_size': page_size,
                        'next_page': bool(len(data) >= page_size + 1 and page)
                    }
                else:
                    data = {'data': data}
            return data

        def handle_empty(data):
            """Handle data that is falsey."""
            return data or ''

        def process_for_mimetype(data):
            """Serialize data per client mimetype request."""
            if data:
                if g.content_type == 'application/json':
                    data = json.dumps(data)
                elif g.content_type == 'application/octet-stream':  # pragma: no branch
                    transformer = self.config['protobuffers']['dump_many'] if many \
                        else self.config['protobuffers']['dump']
                    data = transformer.dict_to_message(data).SerializeToString()
            return data

        return process_for_mimetype(handle_empty(handle_collections(data)))

    @post_load
    def post_load_func(self, data):
        """Implemented for convention."""
        return data


class QuerystringResource(ErrorHandlingSchema):
    """Schema for resource querystrings."""

    fields = _fields.Str(missing='*')
    allowed_fields = ()

    @validates('fields')
    def validate_fields(self, data):
        """Validate fields."""
        if data != '*':
            requested_fields = data.split(',')
            for field in requested_fields:
                if field not in self.allowed_fields:
                    raise ValidationError('Invalid field: {}'.format(field))

    @pre_load
    def parse_querystring(self, args):
        """Parse arguments from querystring and validate that there aren't any extra args."""
        data = []
        for key, val in args:
            data.append((key, val))
        data = {k: v for k, v in data}

        for k in data.keys():
            if k not in self.fields:
                raise ValidationError(f'{k} is an invalid querystring argument.')

        return data


class QuerystringCollection(QuerystringResource):
    """Schema for collection querystrings."""

    ordering = None

    def __init__(self, *args, **kwargs):
        """Extend init function for QuerystringCollection to allow order and order_by as kwargs."""
        ordering = kwargs.pop('ordering')

        super(QuerystringCollection, self).__init__(*args, **kwargs)

        if ordering:
            self.ordering = ordering
            self.fields['order_by'] = _fields.Str(
                missing=ordering[0][0])
            self.fields['order'] = _fields.Str(
                missing=ordering[0][1][0])

    page = _fields.Str(missing='1')
    page_size = _fields.Int(missing=MAX_PAGE_SIZE,
                            validate=validate.Range(min=1, max=MAX_PAGE_SIZE))

    @validates('page')
    def validate_page(self, data):
        """Validate page, if passed, is positive."""
        if data != '*':
            try:
                page = int(data)
                if MAX_PAGES < page or page <= 0:
                    raise ValidationError('Not a valid page.')
            except ValueError:
                raise ValidationError('Not a valid page.')

    @validates_schema(skip_on_field_errors=True)
    def validate_all_pages(self, data):
        """Validate number of fields if page=* is passed."""
        unconditional_paging = False
        config = getattr(self, 'config', None)
        if config:
            unconditional_paging = bool(config.get('unconditional_paging'))

        if data['page'] == '*':
            if not unconditional_paging:
                fields = data['fields'].split(',')
                if data['fields'] == '*' or len(fields) > 2:
                    raise ValidationError('Maximum two fields allowed for page=*.')

    @validates_schema
    def validate_ordering(self, data):
        """Validate that order_by and order are valid."""
        if self.ordering:
            for entry in self.ordering:
                matching_entry = entry if entry[0] == data['order_by'] else None
                if matching_entry:
                    break
            if not matching_entry:
                raise ValidationError('Not a valid field to order by.')
            elif data['order'] not in matching_entry[1]:
                raise ValidationError('Not a valid order for field.')

    @post_load
    def convert_page_to_int(self, data):
        """Cast page to an int (while handling '*')."""
        data['page'] = None if data['page'] == '*' else int(data['page'])
        return data
