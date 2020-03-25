# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'
from types import SimpleNamespace

from mysql import connector

from arxivdigest.core.config import config_sql

_db = SimpleNamespace()
_db.connection = None


def get_connection():
    """Returns an active database connection."""
    if not _db.connection:
        _db.connection = connector.connect(**config_sql)
    if not _db.connection.is_connected():
        _db.connection.reconnect()
    return _db.connection
