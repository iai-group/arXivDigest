# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import mysql.connector
from flask import g
from collections import defaultdict
from core.config import sql_config
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
    sql = "SELECT user_ID FROM users ORDER BY user_ID ASC LIMIT %s, %s"
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
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))
    sql = "SELECT user_ID, firstname, lastname, keywords, registered FROM users WHERE user_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    userList = cur.fetchall()
    users = {}
    for userData in userList:
        users[userData[0]] = {
            'first_name': userData[1],
            'last_name': userData[2],
            'keywords': [x.strip() for x in userData[3].split(",")] if userData[3] else [],
            'registered': userData[4],
            'homepages': [],
            'categories': [],
        }
    sql = "SELECT * FROM user_categories WHERE user_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    usercategories = cur.fetchall()

    for c in usercategories:
        users[c[0]]['categories'].append(c[1])
    sql = "SELECT * FROM user_webpages WHERE user_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    userwebpages = cur.fetchall()

    for c in userwebpages:
        users[c[0]]['homepages'].append(c[1])
    cur.close()

    return users


def getArticleIDs(date):
    """Returns a list of all articleIDs added at the requested date."""
    cur = getDb().cursor()

    sql = "SELECT COUNT(*) FROM articles WHERE datestamp=%s"
    cur.execute(sql, (date,))
    count = cur.fetchone()[0]

    sql = "SELECT article_ID FROM articles WHERE datestamp=%s ORDER BY article_ID ASC"
    cur.execute(sql, (date,))

    articles = {
        'num': count,
        'article_ids': [x[0] for x in cur.fetchall()]
    }
    cur.close()
    return articles


def checkArticlesExists(ids):
    """Takes in a list of articleIDs and returns a list of the IDs that did not
    match any articles in the database."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT article_ID FROM articles WHERE article_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    articles = [x[0] for x in cur.fetchall()]

    cur.close()
    return list(set(ids).difference(articles))


def checkUsersExists(ids):
    """Takes in a list of userIDs and returns a list of the IDs that did not match any users
    in the database."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT user_ID FROM users WHERE user_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    users = [str(x[0]) for x in cur.fetchall()]

    cur.close()
    return list(set(ids).difference(users))


def getArticleData(ids):
    """Takes in a list of articleIDs and returns a nested dictionary
    of data about the articles requested."""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT * FROM articles WHERE article_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    articleList = cur.fetchall()
    articles = {}
    for articleData in articleList:
        articles[articleData[0]] = {
            'title': articleData[1],
            'abstract': articleData[2],
            'doi': articleData[3],
            'comments': articleData[4],
            'license': articleData[5],
            'journal': articleData[6],
            'date': articleData[7].strftime('%Y-%m-%d'),
            'authors': [],
            'categories': [],
        }
    sql = "SELECT * FROM article_categories WHERE article_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    articleCategories = cur.fetchall()

    for c in articleCategories:
        articles[c[0]]['categories'].append(c[1])
    sql = "SELECT * FROM article_authors WHERE article_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    authors = cur.fetchall()
    authorlist = {x[0]: [] for x in authors}
    format_strings = ','.join(['%s'] * len(authorlist))
    sql = "SELECT * FROM author_affiliations WHERE author_ID IN (%s)" % format_strings
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


def insertRecommendations(recommendations):
    """Takes in a list of tuples containg (userID,articleID,systemID,score,timestamp),
    and inserts them into the system_recomendation table, replacing duplicate primary keys."""
    conn = getDb()
    cur = conn.cursor()
    sql = "REPLACE INTO system_recommendations VALUES (%s, %s, %s, %s, %s, %s)"
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


def getUserRecommendations(ids):
    """Returns recomendationdata for the requested userIDs in this format: {userid:{articleID:[data,data,...]}}"""
    cur = getDb().cursor()
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT * FROM system_recommendations WHERE user_ID IN (%s)" % format_strings
    cur.execute(sql, ids)
    users = defaultdict(lambda: defaultdict(list))
    for u in cur.fetchall():
        val = {'system_id': u[2], 'score': u[3], 'date': u[4]}
        users[u[0]][u[1]].append(val)

    cur.close()
    return users


def getUserFeedback(ids):
    """Returns feedbackdata for the requested userIDs in this format: {userid:date[{articleID:feedback}}
    where articleIDs are sorted by score and feedback is a binary number composite of
    seen_email-bit 0,seen_web-bit 1,clicked_email-bit 2,clicked_web-bit 3, liked-bit 4,
    where each of these booleans represent one bit in the same order as the list.
    """
    cur = getDb().cursor(dictionary=True)
    format_strings = ','.join(['%s'] * len(ids))

    sql = "SELECT user_ID, article_ID, DATE(recommendation_date) AS date, " \
          "seen_email, seen_web, clicked_email, clicked_web, liked, score " \
          "FROM user_recommendations WHERE user_ID IN (%s) ORDER BY score DESC" % format_strings
    cur.execute(sql, ids)
    result = defaultdict(lambda: defaultdict(list))
    for feedback in cur.fetchall():
        user = feedback['user_ID']
        date = str(feedback['date'])
        article = feedback['article_ID']
        feedbackNum = feedback['seen_email'] * 1
        feedbackNum += feedback['seen_web'] * 2
        feedbackNum += feedback['clicked_email'] * 4
        feedbackNum += feedback['clicked_web'] * 8
        feedbackNum += feedback['liked'] * 16
        result[user][date].append({article: feedbackNum})
    return result
