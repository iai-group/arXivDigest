# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from collections import defaultdict
from contextlib import closing

from arxivdigest import database


def get_multileaved_articles(start_user_id, n):
    """Fetches multileaved article recommendations.

    :param start_user_id: The first user id to retrieve
    :param n: Number of users to retrieve recommendations for.
    :return: Nested dict in format user_id: date: article_id: recommendation
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT user_id, DATE(recommendation_date) as date, 
                 article_id, score, explanation 
                 FROM article_feedback NATURAL JOIN users 
                 WHERE user_id between %s AND %s
                 AND DATE(recommendation_date) >= 
                 DATE_SUB(UTC_DATE(), INTERVAL 6 DAY) 
                 AND last_email_date < UTC_DATE()'''
        cur.execute(sql, (start_user_id, start_user_id + n - 1))

        result = defaultdict(lambda: defaultdict(dict))
        for r in cur.fetchall():
            result[r.pop('user_id')][r.pop('date')][r.pop('article_id')] = r
        return result


def get_article_data():
    """Returns a dictionary of article_ids: title and authors."""
    cur = database.get_connection().cursor()
    sql = '''SELECT article_id,title, 
             GROUP_CONCAT(concat(firstname,' ',lastname)  SEPARATOR ', ')
             FROM articles natural left join article_authors
             WHERE datestamp >=DATE_SUB(UTC_DATE(),INTERVAL 8 DAY)
             GROUP BY article_id'''
    cur.execute(sql)
    articles = {x[0]: {'title': x[1], 'authors': x[2]} for x in cur.fetchall()}
    cur.close()
    return articles


def insert_mail_trackers(article_traces):
    """Inserts mail trackers into the article feedback table."""
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''UPDATE article_feedback af, users u
                 SET af.seen_email = CURRENT_TIMESTAMP,
                 af.trace_click_email = %(click_trace)s,
                 af.trace_save_email= %(save_trace)s,
                 u.last_email_date=UTC_DATE()
                 WHERE af.user_id=%(user_id)s AND af.article_id=%(article_id)s
                 AND u.user_id = %(user_id)s'''

        cur.executemany(sql, article_traces)
    connection.commit()
