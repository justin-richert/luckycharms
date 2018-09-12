from flask import Flask

app = Flask(__name__)

from fixtures import content_type  # isort:skip  # noqa
