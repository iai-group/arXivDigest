# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import json
import logging
import os
import sys
from collections import defaultdict

from arxivdigest.connector import ArxivdigestConnector
from elasticsearch import Elasticsearch

from index import run_indexing
from init_index import init_index

file_locations = [
    os.path.expanduser('~') + '/arxivdigest/system_config.json',
    '/etc/arxivdigest/system_config.json',
    os.curdir + '/system_config.json',
]


def get_config_from_file(file_paths):
    """Checks the given list of file paths for a config file,
    returns None if not found."""
    for file_location in file_paths:
        if os.path.isfile(file_location):
            print('Found config file at: {}'.format(
                os.path.abspath(file_location)))
            with open(file_location) as file:
                return json.load(file)
    return {}


config_file = get_config_from_file(file_locations)

API_KEY = config_file.get('api_key', '4c02e337-c94b-48b6-b30e-0c06839c81e6')
API_URL = config_file.get('api_url', 'https://api.arxivdigest.org/')
INDEX = config_file.get('index_name', 'main_index')
ELASTICSEARCH_HOST = config_file.get('elasticsearch_host',
                                     {'host': '127.0.0.1', 'port': 9200})


def get_articles_by_topic(es, topic, index, window_size=7, size=10000):
    """Retrieves articles from the Elasticsearch index mentioning 'topic',
    the 'window_size' is the number of days back in time articles will
    be included from."""
    query = {
        'query': {
            'bool': {
                'must': {
                    'match': {
                        'catch_all': {
                            'query': topic,
                        }
                    }
                },
                'filter': {
                    'range': {
                        'date': {
                            'gte': 'now-{}d'.format(window_size)
                        }
                    }
                }
            }
        }
    }
    res = es.search(index=index, body=query, params={"size": size})
    return res


def make_user_recommendation(es, topics, index, n_topics_explanation=3):
    """Makes recommendations based on list of topics and returns a list of
    articles. The score of each article is calculated as the sum of the score of
    each topics, and the explanation is contains all topics that matched an
    article.
    'n_topics_explanation' is how many of the top topics that will be
    included in the explanation."""
    articles = defaultdict(list)
    for topic in topics:
        topic_search = get_articles_by_topic(es, topic, index)['hits']['hits']
        logger.debug('%d articles matches topic %s', len(topic_search), topic)
        for article in topic_search:
            articles[article['_id']].append((article['_score'], topic))

    result = []
    for article_id, score_topic_list in articles.items():
        sorted_topics = [topic for _, topic in sorted(score_topic_list)]

        explanation = create_explanation(sorted_topics[:n_topics_explanation])
        result.append({'article_id': article_id,
                       'score': sum([score for score, _ in score_topic_list]),
                       'explanation': explanation
                       })
    return result


def create_explanation(topics):
    """"Creates explanation from topics."""
    topics = ['**{}**'.format(topic) for topic in topics]
    last = topics.pop()
    topic_str = ', '.join(topics)
    topic_str += ' and ' + last if topic_str else last
    explanation = 'This article seems to be about {}.'.format(topic_str)
    return explanation


def make_recommendations(es, user_info, interleaved_articles, index,
                         n_articles=10):
    """Makes recommendations for all the users in user_info based on the
    topics in user_info. Searches the elasticsearch index for candidates
    and uses the Elasticsearch score as score.
    'n_articles' is the number of articles to recommend for each user."""
    recommendations = {}
    for user, info in user_info.items():
        if not info['topics']:
            logger.info('User {}: skipped (no topics provided).'.format(user))
            continue
        logger.debug('User %s topics: %s.', user, ', '.join(info['topics']))
        articles = make_user_recommendation(es, info['topics'], index)
        articles = [article for article in articles if article['article_id']
                    not in interleaved_articles[user]]
        articles = sorted(articles, key=lambda k: k['score'], reverse=True)

        recommendations[user] = articles[0:n_articles]
        n_recommended = len(recommendations[user])
        logger.info(
            'User {}: recommended {} articles.'.format(user, n_recommended))
    return recommendations


def recommend(es, arxivdigest_connector, index):
    """Makes and sends recommendations to all users."""
    total_users = arxivdigest_connector.get_number_of_users()
    logger.info(
        'Starting recommending articles for {} users'.format(total_users))
    recommendation_count = 0
    while recommendation_count < total_users:
        user_ids = arxivdigest_connector.get_user_ids(recommendation_count)
        user_info = arxivdigest_connector.get_user_info(user_ids)
        interleaved = arxivdigest_connector.get_interleaved_articles(user_ids)

        recommendations = make_recommendations(es, user_info, interleaved,
                                               index)

        if recommendations:
            arxivdigest_connector.send_article_recommendations(recommendations)
        recommendation_count += len(user_ids)
        logger.info('Processed {} users'.format(recommendation_count))


def run(api_key, api_url, index):
    """Runs the recommender system:
        - Updates index with new articles
        - Fetches user info for all users
        - Creates and sends recommendations for each user
        """
    es = Elasticsearch(hosts=[ELASTICSEARCH_HOST])
    arxivdigest_connector = ArxivdigestConnector(api_key, api_url)
    if not es.indices.exists(index=index):
        logger.info('Creating index')
        init_index(es, index)
    logger.info('Indexing articles from arXivDigest API.')
    run_indexing(es, index, arxivdigest_connector)
    recommend(es, arxivdigest_connector, index)
    logger.info('\nFinished recommending articles.')


if __name__ == '__main__':
    log_levels = {
        'FATAL': 50,
        'ERROR': 40,
        'WARNING': 30,
        'INFO': 20,
        'DEBUG': 10,
    }
    logger = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )
    log_level = config_file.get('log_level', 'INFO').upper()
    logger.setLevel(log_levels.get(log_level, 20))

    run(API_KEY, API_URL, INDEX)
