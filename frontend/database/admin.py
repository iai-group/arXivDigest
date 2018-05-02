# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from mysql import connector
from uuid import uuid4
from frontend.database import getDb


def isAdmin(id):
    '''Returns True if if the user with user_id of id is an admin and false if not.'''
    cur = getDb().cursor()
    cur.execute('SELECT admin FROM users where user_id=%s', (id,))
    admin = cur.fetchone()[0]
    cur.close()
    return True if admin is 1 else False


def getSystems():
    '''Returns list of all recommending systems'''
    cur = getDb().cursor(dictionary=True)
    cur.execute('SELECT * FROM systems')
    data = cur.fetchall()
    cur.close()
    return data


def insertSystem(name):
    '''Inserts a new system into the database, name will be used as Name for the system,
    and using uuid a random API-key is generated. Returns the id of the system if successfull and an error if not.'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'INSERT INTO systems VALUES(null,%s,%s,True)'
    key = str(uuid4())
    cur.execute(sql, (key, name))
    id = cur.lastrowid
    cur.close()
    conn.commit()
    return id


def toggleSystem(systemID, value):
    '''Sets active to value for given system. Returns true if successful, false if unsuccessful'''
    cur = getDb().cursor()
    sql = 'UPDATE systems SET active=%s WHERE system_ID = %s'
    cur.execute(sql, (value, systemID, ))
    if cur.rowcount == 0:
        return False
    getDb().commit()
    cur.close()
    return True
