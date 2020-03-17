# -*- coding: utf-8 -*-
from contextlib import closing

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from collections import defaultdict

import mysql.connector
from flask import g

from arxivdigest.core.config import sql_config

"""This module implements methods which the api uses to interface with the database"""


def getDb():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = mysql.connector.connect(**sql_config)
    return db


def getUserIDs(fromID, max):
    """This method returns the total number of users,
    a list of user ids starting at 'fromID' until 'fromID' + 'max',
    and at which id the results starts."""
    cur = getDb().cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    sql = "SELECT user_id FROM users ORDER BY user_id ASC LIMIT %s, %s"
    count = cur.fetchone()[0]
    cur.execute(sql, (fromID, max))
    userList = cur.fetchall()
    try:
        start = userList[0][1]
    except Exception:
        start = fromID
    users = {
        'num': count,
        'start': start,
        'user_ids': [x[0] for x in userList]
    }
    cur.close()
    return users


def getUsers(ids):
    """Takes in a list of userIDs and returns a nested dictionary
    of data about the users requested."""
    cur = getDb().cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))
    sql = '''SELECT user_id, firstname as first_name, lastname as last_name, 
             registered, organization, dblp_profile, google_scholar_profile,
             semantic_scholar_profile, personal_website
             FROM users WHERE user_id IN (%s)''' % format_strings
    cur.execute(sql, ids)

    users = {}
    for user in cur.fetchall():
        user['categories'] = []
        user['topics'] = []
        users[user.pop('user_id')] = user

    sql = 'SELECT * FROM user_categories WHERE user_id IN (%s)' % format_strings

    cur.execute(sql, ids)
    for category in cur.fetchall():
        users[category['user_id']]['categories'].append(
            category['category_id'])

    sql = '''SELECT ut.user_id, t.topic 
             FROM user_topics ut NATURAL JOIN topics t WHERE user_id IN (%s) 
             AND NOT t.filtered''' % format_strings

    cur.execute(sql, ids)
    for topic in cur.fetchall():
        users[topic.pop('user_id')]['topics'].append(topic['topic'])

    cur.close()
    return users


def get_article_ids_past_seven_days():
    """Returns a list of all article ids added the past 7 days."""
    with closing(getDb().cursor()) as cur:
        sql = '''SELECT article_id FROM articles 
                 WHERE datestamp > date_sub(now(), INTERVAL 1 WEEK)
                 ORDER BY article_id ASC'''
        cur.execute(sql)
        return [x[0] for x in cur.fetchall()]


def checkArticlesExists(ids):
    """Takes in a list of articleIDs and returns a list of the IDs that did not
    match any articles in the database."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT article_id FROM articles WHERE article_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    articles = [x[0] for x in cur.fetchall()]

    cur.close()
    return list(set(ids).difference(articles))


def checkUsersExists(ids):
    """Takes in a list of userIDs and returns a list of the IDs that did not match any users
    in the database."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT user_id FROM users WHERE user_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    users = [str(x[0]) for x in cur.fetchall()]

    cur.close()
    return list(set(ids).difference(users))


def get_article_data(ids):
    """Takes in a list of articleIDs and returns a nested dictionary
    of data about the articles requested."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT * FROM articles WHERE article_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    articleList = cur.fetchall()
    articles = {}
    for article_data in articleList:
        articles[article_data[0]] = {
            'title': article_data[1],
            'abstract': article_data[2],
            'doi': article_data[3],
            'comments': article_data[4],
            'license': article_data[5],
            'journal': article_data[6],
            'date': article_data[7],
            'authors': [],
            'categories': [],
        }
    sql = "SELECT * FROM article_categories WHERE article_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    articleCategories = cur.fetchall()

    for c in articleCategories:
        articles[c[0]]['categories'].append(c[1])
    sql = "SELECT * FROM article_authors WHERE article_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    authors = cur.fetchall()
    authorlist = {x[0]: [] for x in authors}
    format_strings = ','.join(['%s'] * len(authorlist))
    sql = "SELECT * FROM author_affiliations WHERE author_id IN (%s)" % format_strings
    cur.execute(sql, list(authorlist.keys()))
    affiliations = cur.fetchall()

    for a in affiliations:
        authorlist[a[0]].append(a[1])

    for a in authors:
        articles[a[1]]['authors'].append(
            {'firstname': a[2],
             'lastname': a[3],
             'affiliations': authorlist[a[0]]})

    cur.close()
    return articles


def insert_article_recommendations(recommendations):
    """Takes in a list of tuples containg (userID,articleID,systemID,score,timestamp),
    and inserts them into the system_recomendation table, replacing duplicate primary keys."""
    conn = getDb()
    cur = conn.cursor()

    sql = '''REPLACE INTO article_recommendations 
             (user_id, article_id, system_id, explanation, score, recommendation_date) 
             VALUES (%s, %s, %s, %s, %s, %s)'''
    cur.executemany(sql, recommendations)
    cur.close()
    conn.commit()

    return True


def getSystem(apiKey):
    """Returns the systemID and systemname for the given apikey, if the key is invalid
    it returns none."""
    cur = getDb().cursor(dictionary=True)
    cur.execute("SELECT * FROM systems WHERE api_key=%s", (apiKey,))
    result = cur.fetchone()
    cur.close()
    return result


def get_article_recommendations(ids):
    """Returns recomendationdata for the requested userIDs in this format: {userid:{articleID:[data,data,...]}}"""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT * FROM article_recommendations WHERE user_id IN (%s)" % format_strings
    cur.execute(sql, ids)
    users = defaultdict(lambda: defaultdict(list))
    for u in cur.fetchall():
        val = {'system_id': u[2], 'score': u[3], 'date': u[4]}
        users[u[0]][u[1]].append(val)

    cur.close()
    return users


def get_user_feedback_articles(ids):
    """Returns feedbackdata for the requested userIDs in this format: {userid:date[{articleID:feedback}}
    where articleIDs are sorted by score and feedback is a binary number composite of
    seen_email-bit 0,seen_web-bit 1,clicked_email-bit 2,clicked_web-bit 3, liked-bit 4,
    where each of these booleans represent one bit in the same order as the list.
    """
    cur = getDb().cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT user_id, article_id, DATE(recommendation_date) AS date, " \
          "seen_email, seen_web, clicked_email, clicked_web, liked, score " \
          "FROM article_feedback WHERE user_id IN (%s) ORDER BY score DESC" % format_strings
    cur.execute(sql, ids)
    result = defaultdict(lambda: defaultdict(list))
    for feedback in cur.fetchall():
        user = feedback['user_id']
        date = feedback['date']
        article = feedback['article_id']

        article_feedback = {
            'seen_email': feedback['seen_email'],
            'seen_web': feedback['seen_web'],
            'clicked_email': feedback['clicked_email'],
            'clicked_web': feedback['clicked_web'],
            'liked': feedback['liked']
        }

        result[user][date].append({article: article_feedback})
    return result
