# -*- coding: utf-8 -*-


class ArxivdigestConnectorException(Exception):
    """Base class for all ArxivdigestConnector exceptions."""


class ConnectionError(ArxivdigestConnectorException):
    """Unable to establish a connection to the arXivDigest API."""


class ApiKeyError(ArxivdigestConnectorException):
    """There was a problem with the api key."""
