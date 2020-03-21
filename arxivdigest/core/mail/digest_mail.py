# -*- coding: utf-8 -*-
import calendar
from datetime import datetime
from uuid import uuid4

from arxivdigest.core.config import config_email
from arxivdigest.core.config import config_interleave
from arxivdigest.core.mail.mail_server import MailServer
from arxivdigest.database import digest_mail as db
from arxivdigest.database import users_db

RECOMMENDATIONS_PER_USER = config_interleave.get('recommendations_per_user')
SYSTEMS_PER_USER = config_interleave.get('systems_multileaved_per_user')
BATCH_SIZE = config_interleave.get('users_per_batch')
BASE_URL = config_interleave.get('web_address')
ARTICLES_PER_DATE_IN_MAIL = config_interleave.get('articles_per_date_in_email')


def send_digest_mail():
    """Sends emails to users about new recommendations."""
    article_data = db.get_article_data()
    server = MailServer(**config_email)

    for i in range(0, users_db.get_highest_user_id() + BATCH_SIZE, BATCH_SIZE):
        msg = 'Sending mails for users with id between {} and {}'
        print(msg.format(i, i + BATCH_SIZE))

        mail_batch, trace_batch = create_mail_batch(i, article_data)
        if not mail_batch:
            continue

        # mark all articles as seen in database and send all mails
        db.insert_mail_trackers(trace_batch)
        for mail in mail_batch:
            server.send_mail(**mail)

    server.close()


def create_mail_batch(start_id, article_data):
    """ Creates a batch of emails for users starting from 'start_id'.

    :param start_id: The id to start from.
    :param article_data: Data about all the articles that are recommended.
    :return:
        A batch of emails that can be sent by a 'MailServer'
        and a list of traces that should be inserted into the data base, used
        for tracing mail interaction from users.
    """
    users = users_db.get_users(start_id, BATCH_SIZE)
    recommendations = db.get_multileaved_articles(start_id, BATCH_SIZE)
    mail_batch = []
    trace_batch = []
    for user_id, user in users.items():

        top_articles = get_top_articles_each_date(recommendations[user_id])
        articles = {}
        if user['notification_interval'] == 1:
            weekday = datetime.utcnow().date().weekday()
            articles = {weekday: top_articles.get(weekday, [])}
        elif datetime.utcnow().weekday() == 4:
            articles = top_articles

        if not any(articles.values()):  # No articles to notify user about
            msg = 'Skipping user {} because there was no recommendations.'
            print(msg.format(user_id))
            continue

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
                    'subject': 'ArXiv Digest',
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
                             'readlink': '%smail/read/%s/%s/%s' % (
                                 BASE_URL, user_id, article_id, click_trace),
                             'likelink': '%smail/like/%s/%s/%s' % (
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
