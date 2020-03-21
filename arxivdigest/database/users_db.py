# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


from contextlib import closing

from arxivdigest import database


def get_highest_user_id():
    """This method returns the highest userID in the database."""
    with closing(database.get_connection().cursor()) as cur:
        cur.execute('SELECT max(user_id) FROM users')
        return cur.fetchone()[0]


def get_number_of_users():
    """This method returns the number of users in the database."""
    with closing(database.get_connection().cursor()) as cur:
        cur.execute('SELECT count(*) FROM users')
        return cur.fetchone()[0]


def get_users(start_user_id, n):
    """Fetches users.

    :param start_user_id: The first user id to retrieve
    :param n: Number of users to retrieve recommendations for.
    :return: A dictionary of user_ids: {email, name, notification_interval}.
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT user_id, email, firstname as name, notification_interval 
                 FROM users WHERE user_id between %s AND %s'''
        cur.execute(sql, (start_user_id, start_user_id + n - 1))
        return {u.pop('user_id'): u for u in cur.fetchall()}
