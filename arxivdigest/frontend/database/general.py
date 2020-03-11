# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from contextlib import closing

import datetime
from datetime import datetime
from uuid import uuid4

import mysql.connector
from mysql import connector
from mysql.connector import errorcode
from passlib.hash import pbkdf2_sha256

from arxivdigest.frontend.database.db import getDb


def get_user(user_id):
    """Gets userdata.

    :param user_id: Id of user to get.
    :return: User data as dictionary.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT user_ID, email, firstname, lastname, keywords, organization,
             notification_interval, registered, last_email_date,
             last_recommendation_date, dblp_profile, google_scholar_profile,
             semantic_scholar_profile, personal_website
             FROM users WHERE user_ID = %s'''
    cur.execute(sql, (user_id,))
    user = cur.fetchone()
    if not user:
        return None

    sql = '''SELECT u.category_id,c.category_name FROM user_categories u 
             JOIN categories c on u.category_ID=c.category_ID 
             WHERE u.user_id = %s'''
    cur.execute(sql, (user_id,))
    user['categories'] = sorted([[c['category_id'], c['category_name']]
                                 for c in cur.fetchall()])
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
    """Inserts user object into database.

    :param user: User-object to insert.
    :return: ID of inserted user.
    """
    user.hashed_password = pbkdf2_sha256.hash(user.password.encode('utf-8'))
    user.registered = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')

    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = '''INSERT INTO users(email, salted_hash, firstname, lastname,
                 keywords, notification_interval, registered, organization, 
                 dblp_profile, google_scholar_profile, 
                 semantic_scholar_profile, personal_website) 
                 VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cur.execute(sql, (user.email, user.hashed_password, user.first_name,
                          user.last_name, user.keywords, user.digestfrequency,
                          user.registered, user.organization, user.dblp_profile,
                          user.google_scholar_profile,
                          user.semantic_scholar_profile, user.personal_website))

        user_id = cur.lastrowid

        sql = 'INSERT INTO user_categories(user_ID, category_ID) VALUES(%s,%s)'
        cur.executemany(sql, [(user_id, cat_id) for cat_id in user.categories])

    conn.commit()
    return user_id


def insertSystem(system_name, user_id):
    """Inserts a new system into the database, name will be used as Name for the system,
    and using uuid a random API-key is generated. Returns None, key if successfull and an error, None if not."""
    conn = getDb()
    cur = conn.cursor()
    sql = 'INSERT INTO systems VALUES(null, %s, %s, False, %s)'
    key = str(uuid4())
    try:
        cur.execute(sql, (key, system_name, user_id))
    except connector.errors.IntegrityError as e:
        col = str(e).split("key ", 1)[1]
        print(col)
        if col == "'system_name'":
            return "System name already in use by another system.", None
        else:
            return "Error, can not connect to server. Try again later", None
    conn.commit()
    return None, key


def update_user(user_id, user):
    """Update user with user_id. User object contains new info for this user."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = '''UPDATE users SET email = %s, firstname = %s, lastname = %s, 
                 organization = %s, personal_website = %s, dblp_profile = %s,
                 google_scholar_profile = %s, semantic_scholar_profile = %s,  
                 keywords = %s, notification_interval = %s 
                 WHERE user_ID = %s'''
        cur.execute(sql, (user.email, user.first_name, user.last_name,
                          user.organization, user.personal_website,
                          user.dblp_profile, user.google_scholar_profile,
                          user.semantic_scholar_profile, user.keywords,
                          user.digestfrequency, user_id))

        cur.execute('DELETE FROM user_categories WHERE user_ID = %s', [user_id])

        data = [(user_id, category_id) for category_id in user.categories]
        cur.executemany('INSERT INTO user_categories VALUES(%s, %s)', data)
    conn.commit()


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


def store_keyword_feedback(userid, keyword, feedback):
    """Stores the users feedback on a keyword to the db.
    Returns true on success and false on failure"""
    sql = 'INSERT IGNORE INTO keyword_feedback VALUES(%s, %s, %s, %s)'
    conn = getDb()
    cur = conn.cursor()
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
    try:
        cur.execute(sql, (userid, keyword, feedback, formatted_date))
    except:
        cur.close()
        return False
    cur.close()
    conn.commit()
    return True


def get_keyword_feedback(userid, keyword):
    """Checks if the user has discarded or approved a keyword earlier.
    Returns approved, discarded or no feedback"""
    sql = 'SELECT feedback FROM keyword_feedback WHERE user_ID = %s AND keyword = %s'
    conn = getDb()
    cur = conn.cursor()
    try:
        cur.execute(sql, (userid, keyword))
    except Exception as e:
        cur.close()
        return "no feedback"
    feedback = cur.fetchone()
    cur.close()
    if feedback == None:
        return "no feedbCK"
    return feedback[0]


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


def get_keyword_feedback_user(user_id):
    """ Gets all the feedback on keywords from given user.
    :param user_id: User to get feedback for.
    :return: List of feedback instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT keyword, feedback, datestamp FROM  keyword_feedback 
             WHERE user_ID = %s'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_freetext_feedback(user_id):
    """Get freetext feedback from given user.
    :param user_id: User to get feedback for.
    :return: List of feedback instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT article_ID, type, feedback_text 
             FROM feedback WHERE user_ID = %s'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_article_recommendations(user_id):
    """Get system recommendations for given user. Includes user interaction data
    if the recommendation has been shown to the user.

    :param user_id: User to get feedback for.
    :return: List of system recommendation instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT sr.article_ID, s.system_name, sr.explanation, 
             sr.score AS system_score, ur.score AS recommendation_order,
             ur.seen_email, ur.seen_web, ur.clicked_email, ur.clicked_web,
             ur.liked, sr.recommendation_date
             FROM system_recommendations sr 
             NATURAL JOIN systems s
             LEFT JOIN user_recommendations ur 
             ON sr.article_ID = ur.article_ID 
             AND sr.user_ID = ur.user_ID
             AND sr.system_ID = ur.system_ID
             WHERE sr.user_ID = %s
             ORDER BY sr.recommendation_date desc,
             s.system_name desc, sr.score desc'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_systems(user_id):
    """Gets systems belonging to a user.

    :param user_id: User to get feedback for.
    :return: List of system dictionaries.
    """
    with closing(getDb().cursor(dictionary=True)) as cur:
        sql = '''SELECT system_ID, system_name, api_key, active
                 FROM systems WHERE user_ID = %s'''
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def get_all_userdata(user_id):
    """Get all data for the given user as a dictionary.

    :param user_id: Id of the user to retrieve data for.
    :return: Dictionary of userdata.
    """

    return {'user': get_user(user_id),
            'freetext_feedback': get_freetext_feedback(user_id),
            'topic_recommendations': get_keyword_feedback_user(user_id),
            'article_recommendations': get_article_recommendations(user_id),
            'systems': get_systems(user_id)}


def get_user_systems(user_id):
    """Gets systems belonging to a user."""
    conn = getDb()
    cur = conn.cursor(dictionary=True)
    sql = '''select system_ID, api_key, active, email, firstname, lastname,
          organization, system_name from systems left join users on 
          users.user_ID = systems.user_ID where users.user_ID = %s'''
    cur.execute(sql, (user_id,))
    systems = cur.fetchall()
    cur.close()
    return systems
