# -*- coding: utf-8 -*-
from mysql import connector
from frontend.database.db import getDb


def getLikedArticles(userid, interval, order, start, n):
    '''Returns liked articles for user with userid and total number of liked articles in the result set. Interval is the number of days before today which should be included in the result,
    order should be one of "titleasc","titledesc","scoreasc" and "scoredesc" and decides the order the resulting articles are sorted,
    start the position in the result set the returned result begins at, and n is the number of recomendations returned.'''
    cur = getDb().cursor(dictionary=True)
    orders = {'titleasc': 'title ASC', 'titledesc': 'title DESC',
              'scoreasc': 'score ASC', 'scoredesc': 'score DESC'}

    # IMPORTANT sanitizes order, against sql injection
    order = orders.get(order.lower(), 'recommendation_date DESC')
    sql = '''SELECT SQL_CALC_FOUND_ROWS article_ID,liked,title,abstract, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ', ') as authors
    FROM user_recommendations
    NATURAL JOIN articles NATURAL JOIN article_authors
    WHERE user_ID = %s AND liked=true AND DATE(recommendation_date) >= DATE_SUB(UTC_DATE(), INTERVAL %s DAY)
    group by article_ID ORDER BY {} LIMIT %s,%s'''.format(order)
    cur.execute(sql, (userid, interval, start, n,))
    articles = cur.fetchall()
    cur.execute('SELECT FOUND_ROWS() as total',)
    total = cur.fetchone()['total']
    cur.close()

    return articles, total


def getUserRecommendations(userid, interval, order, start, n):
    '''Returns recommended articles for user with userid and total number of recomendations in the result set. Interval is the number of days before today which should be included in the result,
    order should be one of "titleasc","titledesc","scoreasc" and "scoredesc" and decides the order the resulting articles are sorted,
    start the position in the result set the returned result begins at, and n is the number of recomendations returned.'''
    cur = getDb().cursor(dictionary=True)
    orders = {'titleasc': 'title ASC', 'titledesc': 'title DESC',
              'scoreasc': 'score ASC', 'scoredesc': 'score DESC'}

    # IMPORTANT sanitizes order, against sql injection
    order = orders.get(order.lower(), 'score DESC')
    sql = '''SELECT SQL_CALC_FOUND_ROWS article_ID,liked,title,abstract,explanation, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ", ") as authors
    FROM user_recommendations
    NATURAL JOIN articles NATURAL JOIN article_authors
    WHERE user_ID = %s AND DATE(recommendation_date) >= DATE_SUB(UTC_DATE(), INTERVAL %s DAY)
    group by article_ID ORDER BY {} LIMIT %s,%s'''.format(order)
    cur.execute(sql, (userid, interval, start, n,))

    articles = cur.fetchall()
    cur.execute('SELECT FOUND_ROWS() as total',)
    total = cur.fetchone()['total']
    cur.close()

    return articles, total


def likeArticle(articleId, userid, setTo):
    '''Sets liked to setTo for given article and user. Returns true if successful like, false if unsuccessful'''
    cur = getDb().cursor()
    sql = 'UPDATE user_recommendations SET liked=%s WHERE article_ID = %s AND user_ID = %s'
    cur.execute(sql, (setTo, articleId, userid, ))
    if cur.rowcount == 0:
        return False
    getDb().commit()
    cur.close()
    return True


def likeArticleEmail(articleId, userid, trace):
    '''Sets liked to true for given article,user and trace. Returns True on succes and False on failure.'''
    conn = getDb()
    cur = conn.cursor()
    result = 0
    sql = 'UPDATE user_recommendations SET liked=True WHERE article_ID = %s AND user_ID = %s AND trace_like_email = %s'
    cur.execute(sql, (articleId, userid, trace))
    result = cur.rowcount

    cur.close()
    conn.commit()

    return True if result > 0 else False


def clickedArticleEmail(articleId, userid, trace):
    '''Sets clicked_email to true for given article,user and trace. Returns True on success and False on failure.'''
    conn = getDb()
    cur = conn.cursor()

    sql = 'UPDATE user_recommendations SET clicked_email=True WHERE article_ID = %s AND user_ID = %s AND trace_click_email = %s'
    cur.execute(sql, (articleId, userid, trace))
    result = cur.rowcount

    cur.close()
    conn.commit()

    return True if result > 0 else False


def clickArticle(articleId, userid):
    '''Sets clicked_web to true for given article and user. Returns True on success.'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'UPDATE user_recommendations SET clicked_web=True WHERE article_ID = %s AND user_ID = %s'

    cur.execute(sql, (articleId, userid, ))
    cur.close()
    conn.commit()
    return True


def seenArticle(articles):
    '''Sets seen_web to true for given articles and useres. Returns True on success.
    <articles> should be a list of tuples: [(article,user),(article,user)].'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'UPDATE user_recommendations SET seen_web=True WHERE article_ID=%s AND user_ID = %s'
    cur.executemany(sql, articles)
    cur.close()
    conn.commit()
    return True
