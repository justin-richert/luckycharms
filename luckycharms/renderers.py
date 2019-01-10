"""Module containing any custom render module logic used by luckycharms."""
import json

from flask_exceptions import BadRequest


class BaseRenderer:
    """Class to be plugged in as render_module on BaseModelSchema."""

    @staticmethod
    def loads(val):
        """Invocated when implementing schema class calls `loads`."""
        try:
            val = json.loads(val) if val else {}
        except json.JSONDecodeError:
            raise BadRequest(message='Tried to deserialize invalid json data.')
        return val

    @staticmethod
    def dumps(val):
        """Invocated when implementing schema class calls `dumps`."""
        val = val or ''
        if val:
            try:
                val = json.dumps(val or '')
            except TypeError:  # pragma: no cover
                raise BadRequest(message='Tried to serialize invalid json data.')
        return val
