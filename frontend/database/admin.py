__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from mysql import connector
from uuid import uuid4
from frontend.database import getDb
import datetime


def isAdmin(id):
    '''Returns True if if the user with user_id of id is an admin and false if not.'''
    cur = getDb().cursor()
    cur.execute('SELECT admin FROM users where user_id=%s', (id,))
    admin = cur.fetchone()[0]
    cur.close()
    return True if admin is 1 else False


def getSystems():
    '''Returns list of all recommending systems'''
    cur = getDb().cursor(dictionary=True)
    cur.execute('SELECT * FROM systems')
    systems = cur.fetchall()
    cur.close()
    return systems


def insertSystem(name):
    '''Inserts a new system into the database, name will be used as Name for the system,
    and using uuid a random API-key is generated. Returns the id of the system if successful and False if not.'''
    conn = getDb()
    cur = conn.cursor()
    sql = 'INSERT INTO systems VALUES(null,%s,%s,True)'
    key = str(uuid4())
    try:
        cur.execute(sql, (key, name))
    except connector.errors.IntegrityError:
        return False
    id = cur.lastrowid
    cur.close()
    conn.commit()
    return id


def toggleSystem(systemID, value):
    '''Sets active to value for given system. Returns true if successful, false if unsuccessful'''
    cur = getDb().cursor()
    sql = 'UPDATE systems SET active=%s WHERE system_ID = %s'
    cur.execute(sql, (value, systemID, ))
    if cur.rowcount == 0:
        return False
    getDb().commit()
    cur.close()
    return True


def getUserStatistics():
    '''Returns statistics about  the users'''
    cur = getDb().cursor()
    sql = 'select count(*), DATE(registered) from users group by DATE(registered) order by registered desc limit 30'
    cur.execute(sql)
    usersByDate = cur.fetchall()
    cur.execute('SELECT count(*) from users')
    total = cur.fetchall()[0][0]

    today = datetime.datetime.today()
    dateList = [(today - datetime.timedelta(days=x)).strftime("%Y-%m-%d")
                for x in range(0, 30)]
    i = 0
    users = []
    for x in dateList:
        if str(usersByDate[i][1]) == x:
            users.append(usersByDate[i][0])
            i += 1
        else:
            users.append(0)

    users.reverse(),
    dateList.reverse(),
    result = {'users': users,
              'dates': dateList,
              'total': total}
    cur.close()
    return result


def getArticleStatistics():
    '''Returns statistics about the articles '''
    cur = getDb().cursor()
    sql = 'select count(*), datestamp from articles group by datestamp order by datestamp desc limit 30'
    cur.execute(sql)
    articlesByDate = cur.fetchall()
    cur.execute('SELECT count(*) from articles')
    total = cur.fetchall()[0][0]

    today = datetime.datetime.today()
    dateList = [(today - datetime.timedelta(days=x)).strftime("%Y-%m-%d")
                for x in range(0, 30)]
    i = 0
    articles = []
    for x in dateList:
        if i < len(articlesByDate) and str(articlesByDate[i][1]) == x:
            articles.append(articlesByDate[i][0])
            i += 1
        else:
            articles.append(0)

    articles.reverse(),
    dateList.reverse(),
    result = {'articles': articles,
              'dates': dateList,
              'total': total}
    cur.close()
    return result
