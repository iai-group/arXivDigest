__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import mysql.connector
import datetime
from models.user import User
from flask import g
from mysql import connector
from uuid import uuid4
import bcrypt
from config import config
from database.db import getDb


def getUser(id):
    '''Return user as a dictionary. Include webpages and categories as sub dictionaries'''
    cur = getDb().cursor()
    cur.execute('SELECT * FROM USERS WHERE user_ID = %s', (id,))
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
    '''Hash and update password to user with id. Returns True on success"'''
    conn = getDb()
    cur = conn.cursor()
    passwordsql = 'UPDATE users SET salted_hash = %s WHERE user_ID = %s'
    password = password.encode('utf-8')
    hashedPassword = bcrypt.hashpw(password, bcrypt.gensalt())
    cur.execute(passwordsql, (hashedPassword, id,))
    cur.close()
    conn.commit()
    return True


def insertUser(user):
    '''Insert user object, webpages and categories into database. Return error or users id'''
    conn = getDb()
    cur = conn.cursor()
    usersql = 'INSERT INTO USERS VALUES(null,%s,%s,%s,%s,%s,%s,%s,false)'
    webpagesql = 'INSERT INTO user_webpages VALUES(%s,%s)'
    categoriesql = 'INSERT INTO user_categories VALUES(%s,%s)'

    userCategories = [(user.email, x) for x in user.categories]
    userWebpages = [(user.email, x) for x in user.webpages]

    password = user.password.encode('utf-8')
    user.hashedPassword = bcrypt.hashpw(password, bcrypt.gensalt())
    curdate = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    cur.execute(usersql, (user.email, user.hashedPassword,
                          user.firstName, user.lastName, user.keywords, user.digestfrequency, curdate))
    id = cur.lastrowid
    userCategories = [(id, x) for x in user.categories]
    userWebpages = [(id, x) for x in user.webpages]
    cur.executemany(webpagesql, userWebpages)
    cur.executemany(categoriesql, userCategories)

    cur.close()
    conn.commit()

    return id


def updateUser(userid, user):
    '''Update user with userid. User object contains new info for this user. Returns True on Success'''
    conn = getDb()
    cur = conn.cursor()
    usersql = 'UPDATE users SET email = %s, firstname = %s, lastname = %s, keywords = %s, notification_interval = %s WHERE user_ID = %s'
    webpagesql = 'INSERT INTO user_webpages VALUES(%s,%s)'
    categoriesql = 'INSERT INTO user_categories VALUES(%s,%s)'

    userCategories = [(user.email, x) for x in user.categories]
    userWebpages = [(user.email, x) for x in user.webpages]

    cur.execute(usersql, (user.email, user.firstName,
                          user.lastName, user.keywords, user.digestfrequency, userid))
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
    '''Checks if users password is correct. Returns userid if correct password, none if user does not exists and
    false if incorrect password'''
    cur = getDb().cursor()
    sql = 'SELECT user_ID,salted_Hash FROM users WHERE email = %s'
    cur.execute(sql, (email,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return None
    if bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
        return user[0]
    return False


def userExist(email):
    '''Checks if email is already in use by another user. Returns True if in use and False if not.'''
    cur = getDb().cursor()
    sql = 'SELECT EXISTS(SELECT user_ID FROM users WHERE email = %s)'
    cur.execute(sql, (email,))
    exists = cur.fetchone()[0]
    cur.close()
    return False if exists is 0 else True


def getCategoryNames():
    '''Returns list of article categories avaiable in the database'''
    cur = getDb().cursor()
    cur.execute('SELECT category_ID,category_name FROM categories')
    data = cur.fetchall()
    cur.close()
    return [[x[0], x[1]] for x in data]
