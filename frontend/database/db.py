# -*- coding: utf-8 -*-
from flask import g
from mysql import connector
from frontend.config import config


def getDb():
    '''Sets up a database connection.'''
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connector.connect(**config.get('sql_config'))
    return db
