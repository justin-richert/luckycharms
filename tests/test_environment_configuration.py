import contextlib
import importlib
import json
import os

import flask_exceptions
import pytest
from marshmallow import fields

from conftest import app
from luckycharms import base


@pytest.fixture(
    scope='function',
    autouse=True,
)
def environment_variables(request):

    prev_max_pages = os.environ.get('LUCKYCHARMS_MAX_PAGES')
    prev_max_page_size = os.environ.get('LUCKYCHARMS_MAX_PAGE_SIZE')
    prev_show_errors = os.environ.get('LUCKYCHARMS_SHOW_ERRORS')

    max_pages = 50
    max_page_size = 25
    show_errors = True
    if hasattr(request, 'param'):
        max_pages = str(request.param.get('max_pages') or max_pages)
        max_page_size = str(request.param.get('max_page_size') or max_page_size)
        show_errors = str(request.param.get('show_errors') or show_errors)

    os.environ['LUCKYCHARMS_MAX_PAGES'] = max_pages
    os.environ['LUCKYCHARMS_MAX_PAGE_SIZE'] = max_page_size
    os.environ['LUCKYCHARMS_SHOW_ERRORS'] = show_errors
    importlib.reload(base)

    max_pages = int(max_pages)
    max_page_size = int(max_page_size)
    show_errors = True if show_errors in ['True', 'true'] else False
    yield max_pages, max_page_size, show_errors

    if prev_max_pages:
        os.environ['LUCKYCHARMS_MAX_PAGES'] = prev_max_pages
    else:
        del os.environ['LUCKYCHARMS_MAX_PAGES']

    if prev_max_page_size:
        os.environ['LUCKYCHARMS_MAX_PAGE_SIZE'] = prev_max_page_size
    else:
        del os.environ['LUCKYCHARMS_MAX_PAGE_SIZE']

    if prev_show_errors:
        os.environ['LUCKYCHARMS_SHOW_ERRORS'] = prev_show_errors
    else:
        del os.environ['LUCKYCHARMS_SHOW_ERRORS']


@pytest.mark.parametrize(
    'environment_variables',
    [{'max_pages': None}, {'max_pages': 2}],
    indirect=True
)
def test_max_pages(environment_variables):

    max_pages, _, _ = environment_variables

    class TestSchema(base.BaseModelSchema):
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

    with app.test_request_context('/?page=5'):
        ctx_mgr = contextlib.suppress() if max_pages == 50 \
            else pytest.raises(flask_exceptions.BadRequest)
        with ctx_mgr:
            result = business_logic()
        if max_pages == 2:
            assert ctx_mgr.excinfo.value.message == 'page: Not a valid page.'
        else:
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


@pytest.mark.parametrize(
    'environment_variables',
    [{'max_page_size': None}, {'max_page_size': 1}],
    indirect=True
)
def test_max_page_size(environment_variables):

    _, max_page_size, _ = environment_variables

    class TestSchema(base.BaseModelSchema):
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
        # default for when max_page_size is None
        if max_page_size == 25:
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
        else:
            assert json.loads(result) == {
                'data': [
                    {
                        'a': 1,
                        'b': 'One'
                    },
                ],
                'next_page': True,
                'page_size': 1
            }


@pytest.mark.parametrize(
    'environment_variables',
    [{'show_errors': True}, {'show_errors': False}],
    indirect=True
)
def test_show_errors(environment_variables):

    _, _, show_errors = environment_variables

    class TestSchema(base.BaseModelSchema):
        a = fields.Int()
        b = fields.String()

    @TestSchema()
    def business_logic(*args, **kwargs):
        return {
            'a': 2,
            'b': 'Two'
        }

    # LUCKYCHARMS_SHOW_ERRORS set to True (see top of test file); msg set on exceptions
    with app.test_request_context(
            '/',
            method='POST',
            data=json.dumps({'a': 2, 'b': 2}),
            headers={'Content-Type': 'application/json'}
            ):
        with pytest.raises(flask_exceptions.BadRequest) as excinfo:
            business_logic()
        expected_message = 'b: Not a valid string.' if show_errors else ''
        assert excinfo.value.message == expected_message
