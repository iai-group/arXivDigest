# -*- coding: utf-8 -*-
'''This module implements methods which the batchprocess uses to interface with the database'''
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'
from collections import defaultdict


def getSystemRecommendations(db, startUserID, n):
    '''This method returns user_ID, system_ID and article_ID in a structure like this:
    {user_ID:{system_ID:[article_IDs]}}.
    '''
    cur = db.cursor()
    sql = '''SELECT user_ID,System_ID, article_ID FROM system_recommendations NATURAL JOIN users WHERE user_ID between %s AND %s
    AND DATE(recommendation_date) = UTC_DATE()
    AND last_recommendation_date < UTC_DATE() ORDER BY score DESC'''
    cur.execute(sql, (startUserID, startUserID+n-1))
    result = defaultdict(lambda: defaultdict(list))
    for r in cur.fetchall():
        result[r[0]][r[1]].append(r[2])
    cur.close()
    return result


def insertUserRecommendations(db, recommendations):
    '''Inserts the recommended articles into database'''
    cur = db.cursor()
    sql = 'INSERT INTO user_recommendations VALUES(%s,%s,%s,%s,%s,0,0,0,0,0,0,0)'
    cur.executemany(sql, recommendations)
    users = {str(x[0]) for x in recommendations}
    users = ','.join(users)
    sql = 'UPDATE users SET last_recommendation_date=UTC_DATE() WHERE user_ID in (%s)' % users
    try:
        cur.execute(sql)
    except Exception:
        print(cur.statement)
        raise
    db.commit()
    cur.close()


def getUserRecommendations(db, startUserID, n):
    '''This method returns user_ID, system_ID and article_ID in a structure like this:
    {user_ID:{date:{article_IDs:score}}.
    '''
    cur = db.cursor()
    sql = '''SELECT user_ID, DATE(recommendation_date), article_ID,  score FROM user_recommendations NATURAL JOIN users 
    WHERE user_ID between %s AND %s
    AND DATE(recommendation_date) >= DATE_SUB(UTC_DATE(), INTERVAL 6 DAY) 
    AND last_email_date < UTC_DATE()'''
    cur.execute(sql, (startUserID, startUserID+n-1))
    result = defaultdict(lambda: defaultdict(dict))
    for r in cur.fetchall():
        result[r[0]][r[1]][r[2]] = r[3]
    cur.close()
    return result


def getUsers(db, startUserID, n):
    '''This method returns user_ID, name, notification_interval and email in a dictionary.'''
    cur = db.cursor()
    sql = 'SELECT user_ID,email,firstname,notification_interval FROM users WHERE user_ID between %s AND %s'
    cur.execute(sql, (startUserID, startUserID+n-1))
    users = {x[0]: {'email': x[1], 'name': x[2], 'notification_interval': x[3]}
             for x in cur.fetchall()}
    cur.close()
    return users


def getNumberOfUsers(db):
    '''This method returns the number of users in the database.'''
    cur = db.cursor()
    sql = 'SELECT count(*) FROM users'
    cur.execute(sql)
    users = cur.fetchone()[0]
    cur.close()
    return users


def getHighestUserID(db):
    '''This method returns the highest userID in the database.'''
    cur = db.cursor()
    sql = 'SELECT max(user_id) FROM users'
    cur.execute(sql)
    users = cur.fetchone()[0]
    cur.close()
    return users


def getArticleData(db):
    '''Returns article data with authors in a dictionary'''
    cur = db.cursor()
    sql = '''SELECT article_ID,title, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ', ') FROM article_authors natural join articles
    WHERE datestamp >=DATE_SUB(UTC_DATE(),INTERVAL 8 DAY) GROUP BY article_ID'''
    cur.execute(sql)
    articles = {x[0]: {'title': x[1], 'authors': x[2]} for x in cur.fetchall()}
    cur.close()
    return articles


def setSeenEmail(db, articles):
    '''Updates database field if user sees the email'''
    cur = db.cursor()
    sql = 'UPDATE user_recommendations SET seen_email=true,trace_click_email=%s, trace_like_email=%s WHERE user_ID=%s and article_ID=%s'
    cur.executemany(sql, articles)
    
    users = {str(x[2]) for x in articles}
    users = ','.join(users)
    sql = 'UPDATE users SET last_email_date=UTC_DATE() WHERE user_ID in (%s)' % users
    cur.execute(sql)
    cur.close()
    db.commit()
