# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


from contextlib import closing

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
                 u.notification_interval FROM users u ORDER BY user_id 
                 LIMIT %s OFFSET %s'''
        cur.execute(sql, (limit, offset))
        return {u.pop('user_id'): u for u in cur.fetchall()}
