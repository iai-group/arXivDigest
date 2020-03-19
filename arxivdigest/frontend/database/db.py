# -*- coding: utf-8 -*-
from flask import g
from mysql import connector

from arxivdigest.core.config import config_sql


def getDb():
    """Sets up a database connection."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connector.connect(**config_sql)
    return db
