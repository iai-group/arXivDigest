# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


from contextlib import closing
from uuid import uuid4

from arxivdigest.core import database


def get_number_of_users():
    """This method returns the number of users in the database."""
    with closing(database.get_connection().cursor()) as cur:
        cur.execute('SELECT count(*) FROM users')
        return cur.fetchone()[0]


def get_users(limit, offset):
    """Fetches users in batches.

    :param limit: Number of users to retrieve.
    :param offset: An offset to the first user returned.
    :return: A dictionary of user_ids: {email, name, notification_interval}.
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT u.user_id, u.email, u.firstname as name, 
                 u.notification_interval, unsubscribe_trace FROM users u ORDER BY user_id 
                 LIMIT %s OFFSET %s'''
        cur.execute(sql, (limit, offset))
        return {u.pop('user_id'): u for u in cur.fetchall()}
    
    
def get_users_without_semantic_scholar(limit, offset):
    """Fetch users that have not provided Semantic Scholar profile links in batches.

    :param limit: Number of users to retrieve.
    :param offset: An offset to the first user returned.
    :return: A dictionary {user_id: {firstname, lastname}}.
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT user_id, firstname, lastname
                 FROM users 
                 WHERE semantic_scholar_profile = ""
                 ORDER BY user_id
                 LIMIT %s OFFSET %s'''
        cur.execute(sql, (limit, offset))
        return {u.pop('user_id'): u for u in cur.fetchall()}


def assign_unsubscribe_trace(user_id):
    """Gives a user an unsubscribe trace if they dont have one."""
    trace = str(uuid4())
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''update users set unsubscribe_trace = %s where user_id = %s'''
        cur.execute(sql, (trace, user_id))

    connection.commit()
    return trace