# -*- coding: utf-8 -*-
from contextlib import closing

from flask import g

from arxivdigest.frontend.database.db import getDb


def getSavedArticles(userid, interval, order, start, n):
    '''Returns saved articles for user with userid and total number of saved articles in the result set. Interval is the number of days before today which should be included in the result,
    order should be one of "titleasc","titledesc","scoreasc" and "scoredesc" and decides the order the resulting articles are sorted,
    start the position in the result set the returned result begins at, and n is the number of recomendations returned.'''
    cur = getDb().cursor(dictionary=True)
    orders = {'titleasc': 'title ASC', 'titledesc': 'title DESC',
              'scoreasc': 'score ASC', 'scoredesc': 'score DESC'}

    # IMPORTANT sanitizes order, against sql injection
    order = orders.get(order.lower(), 'recommendation_date DESC')
    sql = '''SELECT SQL_CALC_FOUND_ROWS article_id,saved,title,abstract,explanation, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ', ') as authors
    FROM article_feedback
    NATURAL JOIN articles NATURAL JOIN article_authors
    WHERE user_id = %s AND saved IS NOT NULL AND DATE(recommendation_date) >= DATE_SUB(UTC_DATE(), INTERVAL %s DAY)
    group by article_id ORDER BY {} LIMIT %s,%s'''.format(order)
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
    sql = '''SELECT SQL_CALC_FOUND_ROWS article_id,saved,title,abstract,explanation, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ", ") as authors
    FROM article_feedback
    NATURAL JOIN articles NATURAL JOIN article_authors
    WHERE user_id = %s AND DATE(recommendation_date) >= DATE_SUB(UTC_DATE(), INTERVAL %s DAY)
    group by article_id ORDER BY {} LIMIT %s,%s'''.format(order)
    cur.execute(sql, (userid, interval, start, n,))

    articles = cur.fetchall()
    cur.execute('SELECT FOUND_ROWS() as total',)
    total = cur.fetchone()['total']
    cur.close()

    return articles, total


def saveArticle(articleId, userid, setTo):
    '''Sets saved to setTo for given article and user. Returns true if successful save, false if unsuccessful'''
    cur = getDb().cursor()
    if setTo:
        sql = 'UPDATE article_feedback SET saved=CURRENT_TIMESTAMP WHERE article_id = %s AND user_id = %s'
    else:
        sql = 'UPDATE article_feedback SET saved=null WHERE article_id = %s AND user_id = %s'
    cur.execute(sql, (articleId, userid, ))
    if cur.rowcount == 0:
        return False
    getDb().commit()
    cur.close()
    return True


def saveArticleEmail(articleId, userid, trace):
    '''Sets saved to true for given article,user and trace. Returns True on succes and False on failure.'''
    conn = getDb()
    cur = conn.cursor()
    result = 0
    sql = 'UPDATE article_feedback SET saved=CURRENT_TIMESTAMP WHERE article_id = %s AND user_id = %s AND trace_save_email = %s'
    cur.execute(sql, (articleId, userid, trace))
    result = cur.rowcount

    cur.close()
    conn.commit()

    return True if result > 0 else False


def clickedArticleEmail(articleId, userid, trace):
    '''Sets clicked_email to true for given article,user and trace. Returns True on success and False on failure.'''
    conn = getDb()
    cur = conn.cursor()

    sql = 'UPDATE article_feedback SET clicked_email=CURRENT_TIMESTAMP WHERE article_id = %s AND user_id = %s AND trace_click_email = %s'
    cur.execute(sql, (articleId, userid, trace))
    result = cur.rowcount

    cur.close()
    conn.commit()

    return True if result > 0 else False


def clickArticle(articleId, userid):
    '''Sets clicked_web to true for given article and user. Returns True on success.'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'UPDATE article_feedback SET clicked_web=CURRENT_TIMESTAMP WHERE article_id = %s AND user_id = %s'

    cur.execute(sql, (articleId, userid, ))
    cur.close()
    conn.commit()
    return True


def seenArticle(articles):
    '''Sets seen_web to true for given articles and useres. Returns True on success.
    <articles> should be a list of tuples: [(article,user),(article,user)].'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'UPDATE article_feedback SET seen_web=CURRENT_TIMESTAMP WHERE article_id=%s AND user_id = %s'
    cur.executemany(sql, articles)
    cur.close()
    conn.commit()
    return True


def article_is_recommended_for_user(article_id):
    """Checks if article has been shown to user."""
    with closing(getDb().cursor()) as cur:
        cur.execute('''SELECT EXISTS(SELECT article_id FROM article_feedback 
                       WHERE user_id = %s AND article_id = %s)''',
                    (g.user, article_id))
        return cur.fetchone()[0] == 1


def get_article_feedback(article_id):
    """Checks if article has been shown to user."""
    with closing(getDb().cursor(dictionary=True)) as cur:
        cur.execute('''SELECT * FROM articles NATURAL JOIN article_feedback
                    WHERE article_id = %s AND user_id = %s''',
                    [article_id, g.user])
        return cur.fetchone()
