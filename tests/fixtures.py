import pytest

from conftest import app


@pytest.fixture(autouse=True)
def content_type(request):

    content_type = 'application/json'
    if hasattr(request, 'param'):
        content_type = request.param.get('content_type', 'application/json')

    app.app_ctx_globals_class.content_type = content_type

    yield

    del app.app_ctx_globals_class.content_type
