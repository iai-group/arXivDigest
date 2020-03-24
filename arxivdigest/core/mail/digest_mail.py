# -*- coding: utf-8 -*-
import logging
import math

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import calendar
from collections import defaultdict
from contextlib import closing
from datetime import datetime
from uuid import uuid4

from arxivdigest.core import database
from arxivdigest.core.config import config_email
from arxivdigest.core.config import config_interleave
from arxivdigest.core.database import users_db
from arxivdigest.core.mail.mail_server import MailServer

RECOMMENDATIONS_PER_USER = config_interleave.get('recommendations_per_user')
SYSTEMS_PER_USER = config_interleave.get('systems_multileaved_per_user')
BATCH_SIZE = config_interleave.get('users_per_batch')
BASE_URL = config_interleave.get('web_address')
ARTICLES_PER_DATE_IN_MAIL = config_interleave.get('articles_per_date_in_email')


def send_digest_mail():
    """Sends emails to users about new recommendations."""
    article_data = get_article_data()
    server = MailServer(**config_email)
    n_users = users_db.get_number_of_users()
    n_batches = math.ceil(n_users / BATCH_SIZE)
    for offset in range(0, n_users, BATCH_SIZE):
        batch = int(offset / BATCH_SIZE) + 1
        logging.info('Sending mails for batch {} of {}.'.format(batch,
                                                                n_batches))

        mail_batch, trace_batch = create_mail_batch(offset, article_data)
        if not mail_batch:
            logging.info('Batch {} was empty.'.format(batch))
            continue

        # mark all articles as seen in database and send all mails
        insert_mail_trackers(trace_batch)
        for mail in mail_batch:
            server.send_mail(**mail)
        logging.info('Batch {} sent.'.format(batch))

    server.close()


def create_mail_batch(offset, article_data):
    """ Creates a batch of emails for users starting from 'start_id'.

    :param offset: The id to start from.
    :param article_data: Data about all the articles that are recommended.
    :return:
        A batch of emails that can be sent by a 'MailServer'
        and a list of traces that should be inserted into the database, used
        for tracing mail interaction from users.
    """
    users = users_db.get_users(BATCH_SIZE, offset)
    recommendations = get_multileaved_articles(BATCH_SIZE, offset)
    mail_batch = []
    trace_batch = []
    for user_id, user in users.items():
        top_articles = get_top_articles_each_date(recommendations[user_id])

        articles = {}
        if user['notification_interval'] == 1:
            weekday = datetime.utcnow().date().weekday()
            articles = {weekday: top_articles.get(weekday, [])}
        elif user['notification_interval'] == 7:
            if datetime.utcnow().weekday() == 4:
                articles = top_articles
            else:
                logging.info('User {}: skipped (notification not scheduled '
                             'for today).'.format(user_id))
                continue
        elif user['notification_interval'] == 0:
            logging.info(
                'User {}: skipped (user turned off notifications).'.format(
                    user_id))
            continue

        if not any(articles.values()):  # No articles to notify user about
            logging.info(
                'User {}: skipped (no recommendations).'.format(user_id))
            continue
        logging.info('User {}: added to batch.'.format(user_id))

        mail, trace = create_mail_content(user_id, user, articles, article_data)
        mail_batch.append(mail)
        trace_batch.extend(trace)
    return mail_batch, trace_batch


def create_mail_content(user_id, user, top_articles, article_data):
    """Creates a mail dictionary in the format accepted by `MailServer`.

    :param user_id: ID of user that will receive the mail.
    :param user: Info about user that will receive the mail.
    :param top_articles: Articles to be included in the mail
    :param article_data: Info about the articles
    :return:
    """
    mail_content = {'to_address': user['email'],
                    'subject': 'arXivDigest article recommendations',
                    'template': 'weekly',
                    'data': {'name': user['name'], 'articles': [],
                             'link': BASE_URL}}
    mail_trace = []
    for day, daily_articles in sorted(top_articles.items()):
        articles = []
        for article_id, explanation in daily_articles:
            article = article_data[article_id]
            click_trace = str(uuid4())
            save_trace = str(uuid4())

            articles.append({'title': article.get('title'),
                             'explanation': explanation,
                             'authors': article.get('authors'),
                             'read_link': '%smail/read/%s/%s/%s' % (
                                 BASE_URL, user_id, article_id, click_trace),
                             'save_link': '%smail/save/%s/%s/%s' % (
                                 BASE_URL, user_id, article_id, save_trace)
                             })
            mail_trace.append({'click_trace': click_trace,
                               'save_trace': save_trace,
                               'user_id': user_id,
                               'article_id': article_id})

        mail_content['data']['articles'].append(
            (calendar.day_name[day], articles, day))

    return mail_content, mail_trace


def get_top_articles_each_date(article_recommendations):
    """Creates lists of top articles for each date.

    Creates dictionary with dates as keys and a list of top scoring articles for
    each date as values.

    :param article_recommendations: Articles that has been recommended for the
    user in a nested dictionary with format:
    {date:{ article_id:{'score' : 2, 'explanation' : "string"}}}
    :return: Dictionary with dates as keys and a list of top scoring articles
    for each date as values.
    """
    top_articles = {}
    for day, articles in article_recommendations.items():
        sorted_articles = sorted(articles.items(),
                                 key=lambda a: a[1]['score'],
                                 reverse=True)
        article_list = [(k, v['explanation']) for k, v in sorted_articles]
        top_articles[day.weekday()] = article_list[:ARTICLES_PER_DATE_IN_MAIL]

    return top_articles


def get_multileaved_articles(limit, offset):
    """Fetches multileaved article recommendations.

    :param limit: Number of users to retrieve recommendations for.
    :param offset: An offset to the first user returned.
    :return: Nested dict in format user_id: date: article_id: recommendation
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT user_id, DATE(recommendation_date) as date, 
                 article_id, score, explanation 
                 FROM article_feedback NATURAL JOIN users
                 NATURAL RIGHT JOIN 
                 (SELECT user_id FROM users ORDER BY user_id 
                 LIMIT %s OFFSET %s) limit_u 
                 WHERE DATE(recommendation_date) > 
                 DATE_SUB(UTC_DATE(), INTERVAL 7 DAY) 
                 AND last_email_date < UTC_DATE()'''
        cur.execute(sql, (limit, offset))

        result = defaultdict(lambda: defaultdict(dict))
        for r in cur.fetchall():
            result[r.pop('user_id')][r.pop('date')][r.pop('article_id')] = r
        return result


def get_article_data():
    """Returns a dictionary of article_ids: title and authors."""
    with closing(database.get_connection().cursor()) as cur:
        sql = '''SELECT article_id,title, 
                 GROUP_CONCAT(concat(firstname,' ',lastname)  SEPARATOR ', ')
                 FROM articles NATURAL LEFT JOIN article_authors
                 WHERE datestamp >=DATE_SUB(UTC_DATE(),INTERVAL 8 DAY)
                 GROUP BY article_id'''
        cur.execute(sql)
        return {x[0]: {'title': x[1], 'authors': x[2]} for x in cur.fetchall()}


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
