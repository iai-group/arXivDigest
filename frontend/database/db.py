__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import g
from mysql import connector
from config import config


def getDb():
    '''Sets up a database connection.'''
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connector.connect(**config.get('sql_config'))
    return db
