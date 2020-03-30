# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from collections import defaultdict
from contextlib import closing
from datetime import datetime

from arxivdigest.core import database
from arxivdigest.core.config import config_interleave
from arxivdigest.core.database import users_db 
from arxivdigest.core.interleave.team_draft_multileave import TeamDraftMultiLeaver

TOPICS_PER_USER = config_interleave.get('topics_multileaved_per_batch')
SYSTEMS_PER_USER = config_interleave.get('systems_multileaved_per_user')

def run(user_id):
    """Multileaves topic suggestions for one user and inserts the result
    into the database."""
    interleaving_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    multi_leaver = TeamDraftMultiLeaver(TOPICS_PER_USER,
                                        SYSTEMS_PER_USER)

    suggested_topics = multi_leave_topics(multi_leaver,
                                          user_id, interleaving_time)

    if suggested_topics:
        insert_topic_suggestions(suggested_topics)

def multi_leave_topics(multileaver, user_id, time):
    """Multileaves a number of suggested topics for a user and returns
    the results."""
    topics = get_user_suggested_topics(user_id)
    if not topics:
        return None
    ranking, credit = multileaver.team_draft_multileave(topics)

    topic_recommendations = []
    # prepare results for database insertion
    for index, (topic, system) in enumerate(zip(ranking, credit)):
            score = multileaver.ranking_length - index
            rec = (score, time, user_id, topic, system)

            topic_recommendations.append(rec)
    return topic_recommendations

def get_user_suggested_topics(user_id):
    """Gets suggested topics per system for one user.
    Returns {system_id:[topic_id, topic_id, topic_id, ... ], ...
        } with score decending"""
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''select topic_recommendations.topic_id, 
                topic_recommendations.system_id from 
                topic_recommendations inner join topics on 
                topics.topic_id = topic_recommendations.topic_id 
                left join user_topics on user_topics.topic_id =
                topic_recommendations.topic_id and user_topics.user_id = 
                topic_recommendations.user_id where 
                user_topics.state is NULL and topic_recommendations.user_id
                = %s and topic_recommendations.interleaving_batch is NULL 
                order by topic_recommendations.system_score DESC'''
        cur.execute(sql, (user_id, ))

        rankings = defaultdict(list)
        for row in cur.fetchall():
            topic_id = row['topic_id']
            system_id = row['system_id']

            rankings[system_id].append(topic_id)
        return rankings

def insert_topic_suggestions(suggested_topics):
    """Inserts the score for the interleaved topic suggestions into
    the database along with the datetime they were interleaved"""
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''update topic_recommendations set interleaving_order = %s,
              interleaving_batch = %s where user_id = %s and topic_id = %s
              and system_id = %s'''
        cur.executemany(sql, suggested_topics)
        connection.commit()