"""
webui.scheduler.errors - app exceptions
"""


class UnsupportedDatasetException(Exception):
    """The dataset is unsupported: the dispatcher returned a None
    configuration."""

    def __init__(self, msg):
        Exception.__init__(self, msg)


class UnknownMIMETypeException(Exception):
    """Is not possible to establish the dataset MIME Type."""

    def __init__(self, msg):
        Exception.__init__(self, msg)


class UnknownMagicException(Exception):
    """The magic code returned by the file is unknown"""

    def __init__(self, msg):
        Exception.__init__(self, msg)
