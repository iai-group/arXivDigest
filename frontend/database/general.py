# -*- coding: utf-8 -*-
import collections

__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import mysql.connector
import datetime
from frontend.models.user import User
from flask import g
from mysql import connector
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
from frontend.database.db import getDb
from mysql.connector import errorcode
from datetime import datetime
from collections import defaultdict


def getUser(id):
    """Return user as a dictionary. Include webpages and categories as sub dictionaries"""
    cur = getDb().cursor()
    sql = '''SELECT user_ID, email, salted_hash, firstname, lastname, keywords, 
    notification_interval, registered
    FROM users WHERE user_ID = %s'''
    cur.execute(sql, (id,))
    userData = cur.fetchone()
    if not userData:
        return None

    user = {
        'id': userData[0],
        'email': userData[1],
        'password': userData[2],
        'firstName': userData[3],
        'lastName': userData[4],
        'keywords': userData[5],
        'notificationInterval': userData[6],
        'registered': userData[7],
    }

    cur.execute('SELECT url FROM user_webpages WHERE user_ID = %s',
                (user['id'],))
    user['webpages'] = [x[0] for x in cur.fetchall()]
    sql = 'SELECT u.category_id,c.category_name FROM user_categories u join categories c on u.category_ID=c.category_ID WHERE u.user_id = %s'
    cur.execute(sql, (user['id'],))
    user['categories'] = [[x[0], x[1]] for x in cur.fetchall()]
    cur.close()

    return user


def updatePassword(id, password):
    """Hash and update password to user with id. Returns True on success\""""
    conn = getDb()
    cur = conn.cursor()
    passwordsql = 'UPDATE users SET salted_hash = %s WHERE user_ID = %s'
    password = password.encode('utf-8')
    hashedPassword = pbkdf2_sha256.hash(password)
    cur.execute(passwordsql, (hashedPassword, id,))
    cur.close()
    conn.commit()
    return True


def insertUser(user):
    """Insert user object, webpages and categories into database. Return error or users id"""
    conn = getDb()
    cur = conn.cursor()
    usersql = 'INSERT INTO users VALUES(null,%s,%s,%s,%s,%s,%s,DEFAULT,DEFAULT,%s,false)'
    webpagesql = 'INSERT INTO user_webpages VALUES(%s,%s)'
    categoriesql = 'INSERT INTO user_categories VALUES(%s,%s)'

    userCategories = [(user.email, x) for x in user.categories]
    userWebpages = [(user.email, x) for x in user.webpages]

    password = user.password.encode('utf-8')
    user.hashedPassword = pbkdf2_sha256.hash(password)
    curdate = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    cur.execute(usersql, (user.email, user.hashedPassword,
                          user.firstName, user.lastName, user.keywords,
                          user.digestfrequency, curdate))
    id = cur.lastrowid
    userCategories = [(id, x) for x in user.categories]
    userWebpages = [(id, x) for x in user.webpages]
    cur.executemany(webpagesql, userWebpages)
    cur.executemany(categoriesql, userCategories)

    cur.close()
    conn.commit()

    return id


def insertSystem(system):
    """Inserts a new system into the database, name will be used as Name for the system,
    and using uuid a random API-key is generated. Returns None if successfull and an error if not."""
    conn = getDb()
    cur = conn.cursor()
    sql = 'INSERT INTO systems VALUES(null,%s,%s,%s,%s,%s,False)'
    key = str(uuid4())
    try:
        cur.execute(sql, (key, system.name, system.contact,
                          system.organization, system.email))
    except connector.errors.IntegrityError as e:
        col = str(e).split("key ", 1)[1]
        if col == "'system_name_UNIQUE'":
            return "System name already in use by another system."
        elif col == "'email_UNIQUE'":
            return "Email already in use by another system."

    conn.commit()
    return None


def updateUser(userid, user):
    """Update user with userid. User object contains new info for this user. Returns True on Success"""
    conn = getDb()
    cur = conn.cursor()
    usersql = 'UPDATE users SET email = %s, firstname = %s, lastname = %s, keywords = %s, notification_interval = %s WHERE user_ID = %s'
    webpagesql = 'INSERT INTO user_webpages VALUES(%s,%s)'
    categoriesql = 'INSERT INTO user_categories VALUES(%s,%s)'

    userCategories = [(user.email, x) for x in user.categories]
    userWebpages = [(user.email, x) for x in user.webpages]

    cur.execute(usersql, (user.email, user.firstName,
                          user.lastName, user.keywords, user.digestfrequency,
                          userid))
    cur.execute('DELETE FROM user_webpages WHERE user_ID = %s', (userid,))
    cur.execute('DELETE FROM user_categories WHERE user_ID = %s', (userid,))
    userCategories = [(userid, x) for x in user.categories]
    userWebpages = [(userid, x) for x in user.webpages]
    cur.executemany(webpagesql, userWebpages)
    cur.executemany(categoriesql, userCategories)

    cur.close()
    conn.commit()
    return True


def validatePassword(email, password):
    """Checks if users password is correct. Returns userid if correct password, none if user does not exists and
    false if incorrect password"""
    cur = getDb().cursor()
    sql = 'SELECT user_ID,salted_Hash FROM users WHERE email = %s'
    cur.execute(sql, (email,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return None
    if pbkdf2_sha256.verify(password.encode('utf-8'), user[1].encode('utf-8')):
        return user[0]
    return False


def userExist(email):
    """Checks if email is already in use by another user. Returns True if in use and False if not."""
    cur = getDb().cursor()
    sql = 'SELECT EXISTS(SELECT user_ID FROM users WHERE email = %s)'
    cur.execute(sql, (email,))
    exists = cur.fetchone()[0]
    cur.close()
    return False if exists is 0 else True


def getCategoryNames():
    """Returns list of article categories available in the database"""
    cur = getDb().cursor()
    cur.execute('SELECT category_ID,category_name FROM categories')
    data = cur.fetchall()
    cur.close()
    return [[x[0], x[1]] for x in data]


def get_keywords_from_titles(titles, quantity=1000):
    """Returns a list of keywords for a list of scientific paper titles.
    Can also specify quantity of keywords to return."""
    cur = getDb().cursor(dictionary=True)

    sql = f'''SELECT o.opinion, k.title, k.keyword, k.score FROM keywords k 
              NATURAL LEFT JOIN keyword_opinions o
              WHERE title IN ({','.join(['%s'] * len(titles))}) 
              AND (o.user_ID = %s OR o.user_ID IS NULL) 
              UNION 
              SELECT null, k.title, k.keyword, k.score FROM keywords k   
              WHERE title IN ({','.join(['%s'] * len(titles))})
              ORDER BY score DESC LIMIT %s;'''

    cur.execute(sql, (*titles, g.user, *titles, quantity))
    data = cur.fetchall()
    cur.close()

    if not data:
        raise ValueError('No matching publications in database')

    rows = defaultdict(list)
    for row in data:  # Some keyword-title pairs has two rows
        rows[(row['title'], row['keyword'])].append(row)

    keywords = defaultdict(int)
    for row in rows.values():
        if len(row) > 1:  # Only keep the row containing 'opinion'
            row = row[0] if row[0]['opinion'] else row[1]
        else:
            row = row[0]
        if row['opinion'] == 'discarded':
            continue
        keywords[row['keyword']] += row['score']

    return keywords


def store_keyword_opinion(userid, keyword, opinion):
    """Stores the users opinion on a keyword to the db.
    Returns true on success and false on failure"""
    sql = 'INSERT IGNORE INTO keyword_opinions VALUES(%s, %s, %s, %s)'
    conn = getDb()
    cur = conn.cursor()
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    try:
        cur.execute(sql, (userid, keyword, opinion, formatted_date))
    except:
        cur.close()
        return False
    cur.close()
    conn.commit()
    return True


def get_keyword_opinion(userid, keyword):
    """Checks if the user has discarded or approved a keyword earlier.
    Returns approved, discarded or no opinion"""
    sql = 'SELECT opinion FROM keyword_opinions WHERE user_ID = %s AND keyword = %s'
    conn = getDb()
    cur = conn.cursor()
    try:
        cur.execute(sql, (userid, keyword))
    except Exception as e:
        cur.close()
        return "no opinion"
    opinion = cur.fetchone()
    cur.close()
    if opinion == None:
        return "no opinion"
    return opinion[0]


def insertFeedback(user_id, article_id, type, feedback_text):
    """Inserts feedback into the database. Returns None if successful and an error if not."""
    conn = getDb()
    cur = conn.cursor()
    sql = 'INSERT INTO feedback (user_ID, article_ID, type, feedback_text) VALUES(%s, %s, %s, %s)'
    try:
        cur.execute(sql, (user_id, article_id, type, feedback_text))
    except mysql.connector.errors.IntegrityError as e:
        if e.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return "Unknown article id."
        raise
    conn.commit()
