__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from mysql import connector
from uuid import uuid4
from database.db import getDb


def isAdmin(id):
    '''Returns True if if the user with user_id of id is an admin and false if not.'''
    cur = getDb().cursor()
    cur.execute('SELECT admin FROM users where user_id=%s', (id,))
    admin = cur.fetchone()[0]
    cur.close()
    return True if admin is 1 else False


def getSystems():
    '''Returns list of all recommending systems'''
    cur = getDb().cursor()
    cur.execute('SELECT system_ID, api_key, system_name FROM systems')
    data = cur.fetchall()
    cur.close()
    return [{'id': x[0], 'name':x[2], 'key':x[1]} for x in data]


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
