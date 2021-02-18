# -*- coding: utf-8 -*-
from flask import g

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import datetime
from contextlib import closing
from datetime import datetime
from uuid import uuid4

import mysql.connector
from mysql import connector
from mysql.connector import errorcode
from passlib.hash import pbkdf2_sha256

from arxivdigest.frontend.database.db import getDb
from arxivdigest.core.interleave import multileave_topics


def get_user(user_id):
    """Gets userdata.

    :param user_id: Id of user to get.
    :return: User data as dictionary.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT user_id, email, firstname, lastname, organization,
             notification_interval, registered, last_email_date,
             last_recommendation_date, dblp_profile, google_scholar_profile,
             semantic_scholar_profile, personal_website, show_semantic_scholar_popup
             FROM users WHERE user_id = %s'''
    cur.execute(sql, (user_id,))
    user = cur.fetchone()
    if not user:
        return None
    # Add categories to user
    sql = '''SELECT u.category_id,c.category_name FROM user_categories u 
             NATURAL JOIN categories c WHERE u.user_id = %s'''
    cur.execute(sql, (user_id,))
    user['categories'] = sorted(cur.fetchall(),
                                key=lambda x: x['category_name'])

    # Add topics to user
    sql = '''SELECT t.topic_id, t.topic FROM user_topics ut 
             NATURAL JOIN topics t WHERE user_id = %s AND NOT t.filtered
             and ut.state in ('USER_ADDED','SYSTEM_RECOMMENDED_ACCEPTED')'''
    cur.execute(sql, (user_id,))
    user['topics'] = sorted(cur.fetchall(), key=lambda x: x['topic'])

    # Add Semantic Scholar profile suggestions to user
    sql = '''SELECT semantic_scholar_id, name, score
             FROM semantic_scholar_suggestions
             WHERE user_id = %s
             ORDER BY score'''
    cur.execute(sql, (user_id,))
    user['semantic_scholar_suggestions'] = cur.fetchall()
    cur.close()
    return user


def updatePassword(id, password):
    """Hash and update password to user with id. Returns True on success\""""
    conn = getDb()
    cur = conn.cursor()
    passwordsql = 'UPDATE users SET salted_hash = %s WHERE user_id = %s'
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
                 notification_interval, registered, organization, 
                 dblp_profile, google_scholar_profile, 
                 semantic_scholar_profile, personal_website, unsubscribe_trace) 
                 VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        cur.execute(sql, (user.email, user.hashed_password, user.firstname,
                          user.lastname, user.notification_interval,
                          user.registered, user.organization, user.dblp_profile,
                          user.google_scholar_profile,
                          user.semantic_scholar_profile, user.personal_website, 
                          str(uuid4())))

        user_id = cur.lastrowid

        set_user_categories(user_id, user)
        set_user_topics(user_id, user)

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
                notification_interval = %s 
                 WHERE user_id = %s'''
        cur.execute(sql, (user.email, user.firstname, user.lastname,
                          user.organization, user.personal_website,
                          user.dblp_profile, user.google_scholar_profile,
                          user.semantic_scholar_profile,
                          user.notification_interval, user_id))
        set_user_categories(user_id, user)
        set_user_topics(user_id, user)
    conn.commit()

def set_user_categories(user_id, user):
    """Helper function for setting user categories does not
    commit."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        cur.execute('DELETE FROM user_categories WHERE user_ID = %s', [user_id])
        data = [(user_id, category_id) for category_id in user.categories]
        cur.executemany('INSERT INTO user_categories VALUES(%s, %s)', data)

def set_user_topics(user_id, user):
    """Helper function for setting user topics, does not
    commit."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        cur.executemany('INSERT IGNORE INTO topics(topic) VALUE(%s)',
                        [(t,) for t in user.topics])

        placeholders = ','.join(['%s']*len(user.topics))
        select_topics = '''SELECT topic_id FROM topics where topic
                        in ({})'''.format(placeholders)

        cur.execute(select_topics, user.topics)
        topic_ids = cur.fetchall()

        current_time = datetime.utcnow()
        topic_ids = [t[0] for t in topic_ids]

        topic_update_sql = '''insert ignore into user_topics(user_id, topic_id, state,
                           interaction_time) values(%s, %s, 'USER_ADDED', %s)'''
        cur.executemany(topic_update_sql, [(user_id, t, current_time) for t in topic_ids])

        topic_update_sql = '''update user_topics set state = 'USER_REJECTED', 
                           interaction_time = %s where
                           user_id = %s and state = 'USER_ADDED' and topic_id 
                           not in ({})'''.format(placeholders)
        cur.execute(topic_update_sql, [current_time, user_id, *topic_ids])

        topic_update_sql = '''update user_topics set state = 'SYSTEM_RECOMMENDED_REJECTED', 
                           interaction_time =%s where
                           user_id = %s and state = 'SYSTEM_RECOMMENDED_ACCEPTED' and topic_id 
                           not in ({})'''.format(placeholders)
        cur.execute(topic_update_sql, [current_time, user_id, *topic_ids])

        topic_update_sql = '''update user_topics set state = 'USER_ADDED', 
                           interaction_time = %s where
                           user_id = %s and state in ('SYSTEM_RECOMMENDED_REJECTED', 'EXPIRED', 
                           'REFRESHED') and topic_id in ({})'''.format(placeholders)
        cur.execute(topic_update_sql, [current_time, user_id, *topic_ids])

        topic_update_sql = '''update user_topics set state = 'USER_ADDED', 
                           interaction_time = %s where
                           user_id = %s and state = 'USER_REJECTED' and topic_id 
                           in ({})'''.format(placeholders)
        cur.execute(topic_update_sql, [current_time, user_id, *topic_ids])

def validatePassword(email, password):
    """Checks if users password is correct. Returns userid if correct password, 
    none if user does not exists and false if incorrect password"""
    cur = getDb().cursor()
    sql = 'SELECT user_id,salted_Hash FROM users WHERE email = %s'
    cur.execute(sql, (email,))
    user = cur.fetchone()
    cur.close()

    if not user:
        return None
    if pbkdf2_sha256.verify(password.encode('utf-8'), user[1].encode('utf-8')):
        return user[0]
    return False


def userExist(email):
    """Checks if email is already in use by another user.
     Returns True if in use and False if not."""
    cur = getDb().cursor()
    sql = 'SELECT user_id FROM users WHERE email = %s'
    cur.execute(sql, (email,))
    row = cur.fetchone()
    cur.close()
    if not row:
        return False
    return False if row[0] == g.user else True


def getCategoryNames():
    """Returns list of article categories available in the database"""
    cur = getDb().cursor()
    cur.execute('SELECT category_id,category_name FROM categories')
    data = cur.fetchall()
    cur.close()
    return [[x[0], x[1]] for x in data]


def insertFeedback(user_id, article_id, type, feedback_text, feedback_values):
    """Inserts feedback into the database.

    :param user_id: ID of user that gave feedback or None if unknown.
    :param article_id: ID of article feedback is about if article
    recommendation feedback
    :param type: Type of feedback
    :param feedback_text: Freetext feedback
    :param feedback_values: Dictionary of key: value feedback pairs
    :return None or error string
    """
    conn = getDb()
    cur = conn.cursor()
    feedback_values = ','.join(['{}:{}'.format(k, v)
                                for k, v in feedback_values.items()])

    try:
        cur.execute('''INSERT INTO feedback 
                    (user_id, article_id, type, feedback_text, feedback_values)
                    VALUES(%s, %s, %s, %s, %s)''',
                    (user_id, article_id, type, feedback_text, feedback_values))

    except mysql.connector.errors.IntegrityError as e:
        if e.errno == errorcode.ER_NO_REFERENCED_ROW_2:
            return "Unknown article id."
        raise
    conn.commit()
    cur.close()


def get_freetext_feedback(user_id):
    """Get freetext feedback from given user.
    :param user_id: User to get feedback for.
    :return: List of feedback instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT article_id, type, feedback_text, feedback_values
             FROM feedback WHERE user_id = %s'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_article_recommendations(user_id):
    """Get article recommendations for given user. Includes user interaction
    data if the recommendation has been shown to the user.

    :param user_id: User to get feedback for.
    :return: List of system recommendation instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT sr.article_id, s.system_name, sr.explanation, 
             sr.score AS system_score, ur.score AS recommendation_order,
             ur.seen_email, ur.seen_web, ur.clicked_email, ur.clicked_web,
             ur.saved, sr.recommendation_date
             FROM article_recommendations sr 
             NATURAL JOIN systems s
             LEFT JOIN article_feedback ur 
             ON sr.article_id = ur.article_id 
             AND sr.user_id = ur.user_id
             AND sr.system_id = ur.system_id
             WHERE sr.user_id = %s
             ORDER BY sr.recommendation_date desc,
             s.system_name desc, sr.score desc'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_topic_recommendations(user_id):
    """Get topic recommendations for given user. Includes user interaction data
    if the recommendation has been shown to the user.

    :param user_id: User to get feedback for.
    :return: List of system recommendation instances.
    """
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT topic, system_name, datestamp, system_score, 
             interleaving_order, seen, clicked,  state, interaction_time
             FROM topic_recommendations tr
             NATURAL JOIN topics t
             NATURAL LEFT JOIN user_topics ut
             NATURAL LEFT JOIN systems s
             WHERE user_id = %s
             ORDER BY datestamp desc, system_name desc, system_score desc;'''
    cur.execute(sql, (user_id,))
    return cur.fetchall()


def get_systems(user_id):
    """Gets systems belonging to a user.

    :param user_id: User to get feedback for.
    :return: List of system dictionaries.
    """
    with closing(getDb().cursor(dictionary=True)) as cur:
        sql = '''SELECT system_id, system_name, api_key, active
                 FROM systems WHERE admin_user_id = %s'''
        cur.execute(sql, (user_id,))
        return cur.fetchall()


def get_all_userdata(user_id):
    """Get all data for the given user as a dictionary.

    :param user_id: Id of the user to retrieve data for.
    :return: Dictionary of userdata.
    """

    return {'user': get_user(user_id),
            'freetext_feedback': get_freetext_feedback(user_id),
            'topic_recommendations': get_topic_recommendations(user_id),
            'article_recommendations': get_article_recommendations(user_id),
            'systems': get_systems(user_id)}


def get_user_systems(user_id):
    """Gets systems belonging to a user."""
    conn = getDb()
    cur = conn.cursor(dictionary=True)
    sql = '''select system_id, api_key, active, email, firstname, lastname,
          organization, system_name from systems left join users on 
          users.user_id = systems.admin_user_id where users.user_id = %s'''
    cur.execute(sql, (user_id,))
    systems = cur.fetchall()
    cur.close()
    return systems


def search_topics(search_string, max_results=50):
    """Searches the topics table for topics starting with `search_string`.

    :param search_string: String topics should start with.
    :param max_results: Number of results to return.
    :return: List of topics.
    """
    with closing(getDb().cursor()) as cur:
        sql = '''SELECT topic FROM topics WHERE topic 
        LIKE CONCAT(LOWER(%s), '%') LIMIT %s'''
        cur.execute(sql, (search_string, max_results))
        return [x[0] for x in cur.fetchall()]

def get_user_topics(user_id):
    """Returns list of top nr recommended topics for a user and marks
    these topics as seen."""
    conn = getDb()
    with closing(conn.cursor(dictionary=True)) as cur:
        sql = '''SELECT tr.topic_id, t.topic
                 FROM  topic_recommendations tr INNER JOIN topics t
                 ON t.topic_id = tr.topic_id 
                 LEFT JOIN user_topics ut 
                 ON ut.topic_id = tr.topic_id AND tr.user_id = ut.user_id
                 WHERE tr.user_id = %s 
                 AND ut.state IS NULL 
                 AND tr.interleaving_batch = (
                        SELECT max(interleaving_batch) 
                        FROM topic_recommendations
                        WHERE user_id = %s 
                        AND interleaving_batch > 
                        DATE_SUB(%s, INTERVAL 24 HOUR))
                ORDER BY tr.interleaving_order DESC'''
        cur.execute(sql, (user_id, user_id, datetime.utcnow()))
        topics = cur.fetchall()

        if not topics:
            # Marks any previous suggested topics as expired if any.
            # Then runs topic interleaver for new topics
            clear_suggested_user_topics(user_id,'EXPIRED')
            multileave_topics.run(user_id)
            cur.execute(sql, (user_id, user_id,datetime.utcnow()))
            topics = cur.fetchall()

        seen_sql = '''update topic_recommendations set
                   seen = %s where topic_id = %s
                   and user_id = %s and interleaving_batch is
                   not NULL and seen is NULL'''
        current_time = datetime.utcnow()
        data = [(current_time, topic['topic_id'], user_id) for topic in topics]
        cur.executemany(seen_sql, data)
        conn.commit()

    return topics

def clear_suggested_user_topics(user_id, state):
    """Clears the users current suggested topics by setting the values for that topic
    to the supplied state(REFRESHED/EXPIRED) for that user"""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        select_topics_sql = '''SELECT tr.topic_id 
                               FROM topic_recommendations tr LEFT JOIN 
                               user_topics ut ON ut.topic_id = tr.topic_id 
                               AND ut.user_id = tr.user_id
                               WHERE ut.state IS NULL
                               AND tr.interleaving_batch IS NOT NULL
                               AND tr.user_id = %s'''
        cur.execute(select_topics_sql, (user_id, ))
        topics = cur.fetchall()

        clear_sql = '''insert into user_topics (user_id, topic_id, state, interaction_time)
                    values(%s, %s, %s, %s)'''
        current_time = datetime.utcnow()
        data = [(user_id, int(topic[0]), state, current_time) for topic in topics]
        cur.executemany(clear_sql, data)
        conn.commit()

def update_user_topic(topic_id, user_id, state):
    """Sets interaction time, state and seen flag for the supplied topic
    to the current datetime."""
    conn = getDb()
    with closing(conn.cursor(dictionary=True)) as cur:
        user_topics_sql = '''insert into user_topics values (%s,%s,%s,%s)'''
        topic_recommendations_sql = '''update topic_recommendations set clicked = %s
        where user_id = %s and topic_id = %s and interleaving_order is not null'''
        current_time = datetime.utcnow()
        cur.execute(user_topics_sql, (user_id, topic_id, state, current_time))
        cur.execute(topic_recommendations_sql, (current_time, user_id, topic_id))
        conn.commit()
        return cur.rowcount == 1

def is_activated(user_id):
    """Checks if a user has activated their account. Returns True or false"""
    cur = getDb().cursor()
    cur.execute('SELECT inactive FROM users where user_id=%s', (user_id,))
    inactive = cur.fetchone()[0]
    cur.close()
    return False if inactive is 1 else True

def add_activate_trace(trace, email):
    """Connects the trace from the activation email to the user."""
    conn = getDb()
    cur = conn.cursor()
    sql = '''update users set activate_trace = %s where email = %s'''
    cur.execute(sql, (trace, email))
    conn.commit()
    cur.close()

def activate_user(trace):
    """Activates the user with the supplied trace."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = '''update users set inactive = 0 where activate_trace = %s'''
        cur.execute(sql, (trace, ))
        conn.commit()
        return cur.rowcount == 1

def update_email(email, user_id):
    """Updates the email for a user."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = '''update users set email = %s where user_id = %s'''
        cur.execute(sql, (email, user_id))
        conn.commit()

def update_semantic_scholar(link, user_id):
    """Updates the Semantic Scholar link for a user."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = 'update users set semantic_scholar_profile = %s where user_id = %s'
        cur.execute(sql, (link, user_id))
        conn.commit()
        
def show_semantic_scholar_popup(show_popup: bool, user_id):
    """Sets whether the Semantic Scholar profile suggestion popup should be shown."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = 'update users set show_semantic_scholar_popup = %s where user_id = %s'
        cur.execute(sql, (show_popup, user_id))
        conn.commit()

def delete_semantic_scholar_suggestions(user_id):
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = 'delete from semantic_scholar_suggestions where user_id = %s'
        cur.execute(sql, (user_id,))
        conn.commit()

def get_semantic_scholar_suggestions(user_id):
    conn = getDb()
    with closing(conn.cursor(dictionary=True)) as cur:
        sql = '''SELECT semantic_scholar_id, name, score
                 FROM semantic_scholar_suggestions
                 WHERE user_id = %s
                 ORDER BY score'''
        cur.execute(sql, (user_id,))
        return cur.fetchall()

def log_semantic_scholar_choice(accepted_semantic_scholar_id: int, number_of_suggestions: int, user_id):
    conn = getDb()
    with closing(conn.cursor(dictionary=True)) as cur:
        sql = '''REPLACE INTO semantic_scholar_suggestion_log (user_id, number_of_suggestions, accepted_semantic_scholar_id) 
                 VALUES (%s, %s, %s)'''
        cur.execute(sql, (user_id, number_of_suggestions, accepted_semantic_scholar_id))
        conn.commit()

def digest_unsubscribe(trace):
    """Unsubscribes the user with the supplied trace from the
    digest email and assigns a new unsubscribe trace to the user."""
    conn = getDb()
    with closing(conn.cursor()) as cur:
        sql = '''update users set notification_interval = 0,
              unsubscribe_trace = %s where unsubscribe_trace = %s'''
        cur.execute(sql, (str(uuid4()) , trace))
        conn.commit()
        return cur.rowcount == 1


def get_topic_feedback_by_date(start_date, end_date, system=None):
    """Gets all topic feedback between start and end date."""
    cur = getDb().cursor(dictionary=True)
    sql = '''SELECT tr.user_id, tr.system_id, tr.interleaving_batch, ut.state 
             FROM topic_recommendations tr  JOIN user_topics ut 
             ON tr.user_id = ut.user_id AND tr.topic_id = ut.topic_id
             WHERE tr.interleaving_order IS NOT NULL AND 
             tr.interleaving_batch >= %s AND tr.interleaving_batch <= %s'''
    if system:
        sql += 'AND tr.system_id = %s'
        cur.execute(sql, (start_date, end_date, system))
    else:
        cur.execute(sql, (start_date, end_date))
    return cur.fetchall()
