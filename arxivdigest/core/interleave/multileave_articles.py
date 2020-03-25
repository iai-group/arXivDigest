# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import logging
from collections import defaultdict
from contextlib import closing
from datetime import datetime

from arxivdigest.core import database
from arxivdigest.core.config import config_interleave
from arxivdigest.core.database import users_db
from arxivdigest.core.interleave.team_draft_multileave import TeamDraftMultiLeaver

RECOMMENDATIONS_PER_USER = config_interleave.get('recommendations_per_user')
SYSTEMS_PER_USER = config_interleave.get('systems_multileaved_per_user')
BATCH_SIZE = config_interleave.get('users_per_batch')
ARTICLES_PER_DATE_IN_MAIL = config_interleave.get('articles_per_date_in_email')


def run():
    """Multileaves article recommendations and inserts the new lists into the
    database."""
    interleaving_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    multi_leaver = TeamDraftMultiLeaver(RECOMMENDATIONS_PER_USER,
                                        SYSTEMS_PER_USER)

    n_users = users_db.get_number_of_users()
    logging.info('Starting multileaving for {} users.'.format(n_users))
    for i in range(0, n_users, BATCH_SIZE):

        recommendations = multi_leave_articles(BATCH_SIZE,
                                               i,
                                               multi_leaver,
                                               interleaving_time)
        if recommendations:
            insert_article_recommendations(recommendations)


def multi_leave_articles(limit,
                         offset,
                         multileaver,
                         time):
    """Multileaves the given systemRecommendations and returns
       a list of article_feedback."""
    article_feedback = []
    articles, explanations = get_article_recommendations(limit, offset)
    users = users_db.get_users(limit, offset)
    for user_id in users:
        lists = articles[user_id]
        if not lists:
            logging.info('User {}: skipped (no recommendations).'.format(
                user_id))
            continue

        ranking, credit = multileaver.team_draft_multileave(lists)
        # prepare results for database insertion
        for index, (article, system) in enumerate(zip(ranking, credit)):
            score = multileaver.ranking_length - index
            explanation = explanations[user_id][system][article]
            rec = (user_id, article, system, explanation, score, time)

            article_feedback.append(rec)
        logging.info('User {}: Interleaved {} articles.'.format(user_id,
                                                                len(ranking)))
    return article_feedback


def get_article_recommendations(limit, offset):
    """Fetches article recommendation for articles released the past week.

    :param limit: Number of users to retrieve recommendations for.
    :param offset: An offset to the first user returned.
    :return: Article recommendations (rankings) in the following format
    sorted by score descending:
     {user_id:
        {system_id:[article_id, article_id, article_id, ... ], ...
        }, ...
     }
    And explanations in the format:
         {user_id: {system_id: {article_id: explanation, ...}, ...}, ...}
    """
    with closing(database.get_connection().cursor(dictionary=True)) as cur:
        sql = '''SELECT ar.user_id, ar.system_id, ar.article_id, ar.explanation 
        FROM article_recommendations ar Left JOIN article_feedback  af  
        on ar.article_id = af.article_id AND ar.user_id = af.user_id 
        JOIN users u on ar.user_id = u.user_id
        JOIN articles a on a.article_id = ar.article_id
        RIGHT JOIN (SELECT user_id FROM users ORDER BY user_id 
        LIMIT %s OFFSET %s) limit_u on limit_u.user_id = ar.user_id 
        WHERE af.score is null 
        AND a.datestamp > DATE_SUB(UTC_DATE(), INTERVAL 7 DAY) 
        AND u.last_recommendation_date < UTC_DATE() ORDER BY ar.score DESC;'''
        cur.execute(sql, (limit, offset))

        rankings = defaultdict(lambda: defaultdict(list))
        explanations = defaultdict(lambda: defaultdict(dict))
        for row in cur.fetchall():
            user_id = row['user_id']
            article_id = row['article_id']
            system_id = row['system_id']
            explanation = row['explanation']

            rankings[user_id][system_id].append(article_id)
            explanations[user_id][system_id][article_id] = explanation
        return rankings, explanations


def insert_article_recommendations(recommendations):
    """Inserts the recommended articles into the article feedback table."""
    connection = database.get_connection()
    with closing(connection.cursor(dictionary=True)) as cur:
        sql = '''INSERT INTO article_feedback (user_id, article_id, system_id, 
                 explanation, score, recommendation_date)      
                 VALUES(%s, %s, %s, %s, %s, %s)'''
        cur.executemany(sql, recommendations)

        users = list({x[0] for x in recommendations})
        sql = '''UPDATE users SET last_recommendation_date=UTC_DATE() 
                 WHERE user_id in ({})'''.format(','.join(['%s'] * len(users)))
        cur.execute(sql, users)
        connection.commit()
