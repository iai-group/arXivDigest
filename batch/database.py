'''This module implements methods which the batchprocess uses to interface with the database'''
_author_ = "Øyvind Jekteberg and Kristian Gingstad"
_copyright_ = "Copyright 2018, The ArXivDigest Project"
from collections import defaultdict


def getSystemRecommendations(db, startUserID, max):
    '''This method returns user_ID, system_ID and article_ID in a structure like this:
    {user_ID:{system_ID:[article_IDs]}}.
    '''
    cur = db.cursor()
    sql = 'SELECT user_ID FROM users WHERE last_recommendation_date<= DATE_SUB(CURDATE(), INTERVAL notification_interval DAY) ORDER BY user_ID ASC LIMIT %s, %s'
    cur.execute(sql, (startUserID, max))
    users = cur.fetchall()
    if not users:
        return []
    sql = """SELECT user_ID,System_ID, article_ID FROM system_recommendations NATURAL JOIN users WHERE user_ID between %s AND %s 
    AND DATE(recommendation_date) >= DATE_SUB(CURDATE(), INTERVAL notification_interval-1 DAY) 
    AND last_recommendation_date<= DATE_SUB(CURDATE(), INTERVAL notification_interval DAY) ORDER BY score DESC"""
    cur.execute(sql, (users[0][0], users[-1][0])
                )  # selects the highest and lowest user_ID
    result = defaultdict(lambda: defaultdict(list))
    for r in cur.fetchall():
        result[r[0]][r[1]].append(r[2])
    cur.close()
    return result


def getUsers(db, startUserID, max):
    '''This method returns user_ID, firstname and email in a dictionary.'''
    cur = db.cursor()
    sql = 'SELECT user_ID,email,firstname FROM users WHERE last_recommendation_date<= DATE_SUB(CURDATE(), INTERVAL notification_interval DAY) LIMIT %s, %s'
    cur.execute(sql, (startUserID, max))
    users = {x[0]: {'email': x[1], 'name': x[2]} for x in cur.fetchall()}

    return users


def getArticleData(db):
    '''Returns article data with authors in a dictionary'''
    cur = db.cursor()
    sql = """SELECT article_ID,title, GROUP_CONCAT(concat(firstname," ",lastname)  SEPARATOR ', ') FROM article_authors natural join articles 
    WHERE datestamp >=DATE_SUB(CURDATE(),INTERVAL 8 DAY) GROUP BY article_ID"""
    cur.execute(sql)
    articles = {x[0]: {'title': x[1], 'authors': x[2]} for x in cur.fetchall()}
    cur.close()
    return articles


def setSeenEmail(db, articles):
    '''Updates database field if user sees the email'''
    cur = db.cursor()
    sql = 'UPDATE user_recommendations SET seen_email=true,trace_click_email=%s, trace_like_email=%s WHERE user_ID=%s and article_ID=%s'
    cur.executemany(sql, articles)
    cur.close()
    db.commit()


def insertUserRecommendations(db, recommendations):
    '''Inserts the recommended articles into database'''
    cur = db.cursor()
    sql = 'INSERT INTO user_recommendations VALUES(%s,%s,%s,%s,%s,0,0,0,0,0,0,0)'
    cur.executemany(sql, recommendations)
    db.commit()
