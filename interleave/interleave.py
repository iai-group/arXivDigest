# -*- coding: utf-8 -*-
'''This script interleaves the recommendations from the experimental
   recommender systems and inserts the combined ranking, for each user,
   into the database.
   It also sends out the digest emails to users.
'''

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import calendar
from datetime import datetime
from uuid import uuid4

from mysql import connector

import database as db
from arxivdigest.core.config import email_config
from arxivdigest.core.config import interleave_config
from arxivdigest.core.config import sql_config
from arxivdigest.core.mail.mail_server import MailServer
from tdm import multiLeaver

RECOMMENDATIONS_PER_USER = interleave_config.get('recommendations_per_user')
SYSTEMS_PER_USER = interleave_config.get('systems_multileaved_per_user')
BATCH_SIZE = interleave_config.get('users_per_batch')
BASE_URL = interleave_config.get('webaddress')
ARTICLES_PER_DATE_IN_MAIL = interleave_config.get('articles_per_date_in_email')


def multi_leave_recommendations(article_recommendations, multileaver, time):
    """Multileaves the given systemRecommendations and returns
       a list of article_feedback."""
    article_feedback = []
    for user_id, lists in article_recommendations.items():
        # multileave system recommendations
        recs, systems = multileaver.TDM(lists)
        # prepare results for database insertion
        for index, rec in enumerate(recs):
            score = len(recs) - index

            rec = (user_id, rec["article_id"], systems[index],
                   rec["explanation"], score, time)

            article_feedback.append(rec)
    return article_feedback


def sendMail(conn):
    """Sends emails to users about new recommendations."""
    article_data = db.get_article_data(conn)
    server = MailServer(**email_config)

    for i in range(0, db.getHighestUserID(conn) + BATCH_SIZE, BATCH_SIZE):
        mail_batch, trace_batch = create_mail_batch(i, article_data, conn)
        if not mail_batch:
            continue

        # mark all articles as seen in database and send all mails
        db.setSeenEmail(conn, trace_batch)
        for mail in mail_batch:
            server.send_mail(**mail)

    server.close()


def create_mail_content(user_id, user, top_articles, article_data):
    """Creates a mail dictionary in the format accepted by 'MailServer'.

    :param user_id: ID of user that will receive the mail.
    :param user: Info about user that will receive the mail.
    :param top_articles: Articles that
    :param article_data: Info about the
    :return:
    """
    mail_content = {'to_address': user['email'],
                    'subject': 'ArXiv Digest',
                    'template': 'weekly',
                    'data': {'name': user['name'], 'articles': [],
                             'link': BASE_URL}}
    mail_trace = []
    for day, daily_articles in sorted(top_articles.items()):
        articles = []
        for article_id, explanation in daily_articles:
            article = article_data.get(article_id)
            click_trace = str(uuid4())
            like_trace = str(uuid4())

            articles.append({'title': article.get('title'),
                             'explanation': explanation,
                             'authors': article.get('authors'),
                             'readlink': '%smail/read/%s/%s/%s' % (
                                 BASE_URL, user_id, article_id, click_trace),
                             'likelink': '%smail/like/%s/%s/%s' % (
                                 BASE_URL, user_id, article_id, like_trace)
                             })
            mail_trace.append((click_trace, like_trace, user_id, article_id))

        mail_content['data']['articles'].append(
            (calendar.day_name[day], articles, day))

    return mail_content, mail_trace


def create_mail_batch(start_id, article_data, conn):
    """ Creates a batch of emails for users starting from 'start_id'.

    :param start_id: The id to start from.
    :param article_data: Data about all the articles that are recommended.
    :param conn: Database connection.
    :return:
        A batch of emails that can be sent by a 'MailServer'
        and a list of traces that should be inserted into the data base, used
        for tracing mail interaction from users.
    """
    users = db.getUsers(conn, start_id, BATCH_SIZE)
    article_feedback = db.getUserRecommendations(conn, start_id, BATCH_SIZE)
    mail_batch = []
    trace_batch = []
    for user_id, user in users.items():

        top_articles = get_top_articles_each_date(article_feedback[user_id])

        articles = {}
        if user['notification_interval'] == 1:
            weekday = datetime.utcnow().date().weekday()
            articles = {weekday: top_articles.get(weekday, [])}
        elif datetime.utcnow().weekday() == 4:
            articles = top_articles

        if not any(articles.values()):  # No articles to notify user about
            continue

        mail, trace = create_mail_content(user_id, user, articles, article_data)
        mail_batch.append(mail)
        trace_batch.extend(trace)
    return mail_batch, trace_batch


def get_top_articles_each_date(article_feedback):
    """Creates lists of top articles for each date.

    Creates dictionary with dates as keys and a list of top scoring articles for
    each date as values.

    :param article_feedback: Articles that has been recommended for the user
    in a nested dictionary with format:
    {date:{ article_id:{'score' : 2, 'explanation' : "string"}}}
    :return: Dictionary with dates as keys and a list of top scoring articles
    for each date as values.
    """
    top_articles = {}
    for day, articles in article_feedback.items():
        sorted_articles = sorted(articles.items(),
                                 key=lambda a: a[1]['score'],
                                 reverse=True)
        article_list = [(k, v['explanation']) for k, v in sorted_articles]
        top_articles[day.weekday()] = article_list[:ARTICLES_PER_DATE_IN_MAIL]

    return top_articles


def run():
    """Multileaves system recommendations and inserts the new lists into the
    database, then sends notification email to user."""
    conn = connector.connect(**sql_config)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    ml = multiLeaver(RECOMMENDATIONS_PER_USER, SYSTEMS_PER_USER)
    max_user_id = db.getHighestUserID(conn)

    for i in range(0, max_user_id + BATCH_SIZE, BATCH_SIZE):
        system_recs = db.getSystemRecommendations(conn, i, BATCH_SIZE)
        if system_recs:
            recommendations = multi_leave_recommendations(system_recs, ml, now)
            db.insertUserRecommendations(conn, recommendations)

    sendMail(conn)
    conn.close()


if __name__ == '__main__':
    run()
