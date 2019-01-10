from . import base, test_pb2


class RendererTest(base.BaseResource):
    """Test resource renderer."""

    @staticmethod
    def _get_message():
        """Determines the message to be used during transformation."""

        return test_pb2.Test()
