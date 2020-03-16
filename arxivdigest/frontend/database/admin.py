# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import datetime

from arxivdigest.frontend.database.db import getDb


def isAdmin(id):
    '''Returns True if if the user with user_id of id is an admin and false if not.'''
    cur = getDb().cursor()
    cur.execute('SELECT admin FROM users where user_id=%s', (id,))
    admin = cur.fetchone()[0]
    cur.close()
    return True if admin is 1 else False


def getSystems():
    """Returns list of all recommending systems with null values if
    the systems are not connected to a user."""
    cur = getDb().cursor(dictionary=True)
    cur.execute('''select system_id, api_key, active, email, firstname, lastname, 
                organization, system_name from systems left join users
                on users.user_id = systems.admin_user_id;''')
    systems = cur.fetchall()
    cur.close()
    return systems


def getSystem(ID):
    '''Returns requested system.'''
    cur = getDb().cursor(dictionary=True)
    cur.execute('SELECT * FROM systems where system_id = %s', (ID,))
    data = cur.fetchone()
    cur.close()
    return data


def toggleSystem(systemID, value):
    '''Sets active to value for given system. Returns true if successful, false if unsuccessful'''
    cur = getDb().cursor()
    sql = 'UPDATE systems SET active=%s WHERE system_id = %s'
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


def getAdmins():
    '''Returns admin users id, email and names'''
    cur = getDb().cursor(dictionary=True)
    sql = 'select user_id, email, firstname, lastname from users where admin=1'
    cur.execute(sql)
    admindata = cur.fetchall()
    cur.close()
    return admindata