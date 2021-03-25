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
    

def get_number_of_users_for_suggestion_generation():
    """Gets the number of users that have not provided links to their Semantic Scholar profiles and have not
    previously accepted/declined any suggestions."""
    with closing(database.get_connection().cursor()) as cur:
        sql = '''SELECT count(*)
                 FROM users u LEFT JOIN semantic_scholar_suggestion_log log ON u.user_id=log.user_id
                 WHERE semantic_scholar_profile = "" AND log.user_id IS NULL'''
        cur.execute(sql)
        return cur.fetchone()[0]


def get_users_for_suggestion_generation(limit, offset, all_users=False):
    """Gets the users that have not provided Semantic Scholar profile links and have not previously accepted/declined
    any suggestions.

    :param limit: Number of users to retrieve.
    :param offset: An offset to the first user returned.
    :param all_users: Return all users, regardless of whether they have provided Semantic Scholar profile links
    and/or have previously accepted/declined any suggestions.
    :return: A dictionary {user_id: {firstname, lastname}}.
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT u.user_id, u.firstname, u.lastname
                 FROM users u LEFT JOIN semantic_scholar_suggestion_log log ON u.user_id=log.user_id
                 WHERE %s OR (semantic_scholar_profile = "" AND log.user_id IS NULL)
                 ORDER BY user_id
                 LIMIT %s OFFSET %s'''
        cur.execute(sql, (all_users, limit, offset))
        users = {u['user_id']: u for u in cur.fetchall()}
        for user_id, user_data in users.items():
            sql = '''SELECT t.topic FROM user_topics ut 
                     NATURAL JOIN topics t WHERE user_id = %s AND NOT t.filtered
                     and ut.state in ('USER_ADDED','SYSTEM_RECOMMENDED_ACCEPTED')'''
            cur.execute(sql, (user_id,))
            user_data['topics'] = cur.fetchall()
        return users


def assign_unsubscribe_trace(user_id):
    """Gives a user an unsubscribe trace if they dont have one."""
    trace = str(uuid4())
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''update users set unsubscribe_trace = %s where user_id = %s'''
        cur.execute(sql, (trace, user_id))

    connection.commit()
    return trace