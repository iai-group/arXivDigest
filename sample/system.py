# -*- coding: utf-8 -*-
import logging

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import json
import os
import sys
import urllib
from collections import defaultdict
from urllib import request

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


def get_user_ids(start, api_key, api_url):
    """Queries the arXivDigest API for user ids starting from 'start'. """
    req = request.Request('%susers?from=%d' % (api_url, start),
                          headers={"api-key": api_key})
    resp = request.urlopen(req)
    return json.loads(resp.read())


def get_user_info(user_ids, api_key, api_url, batch_size=100):
    """Queries the arXivDigest API for userdata for the given 'user_ids'."""
    user_info = {}
    for i in range(0, len(user_ids), batch_size):
        user_id_string = ','.join([str(u) for u in user_ids[i:i + batch_size]])
        url = '%suser_info?user_id=%s' % (api_url, user_id_string)
        req = request.Request(url, headers={"api-key": api_key})
        resp = request.urlopen(req)
        user_info.update(json.loads(resp.read())['user_info'])
    return user_info


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


def send_recommendations(recommendations, api_key, api_url, batch_size=100):
    """Sends the recommendations to the arXivDigest API.
    Recommendations should be a dict of user_id, recommendation pairs."""
    recommendations = list(recommendations.items())
    for i in range(0, len(recommendations), batch_size):
        data = json.dumps({'recommendations': dict(
            recommendations[i:i + batch_size])}).encode('utf8')
        req = request.Request(api_url + "/recommendations/articles", data=data,
                              headers={'Content-Type': 'application/json',
                                       "api-key": api_key})
        try:
            request.urlopen(req)
        except urllib.error.HTTPError as e:
            logger.error('Response:', e.read().decode())


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
        expl_str = ', '.join(sorted_topics[:n_topics_explanation])
        explanation = 'This article matches the topics: {}'.format(expl_str)
        result.append({'article_id': article_id,
                       'score': sum([score for score, _ in score_topic_list]),
                       'explanation': explanation
                       })
    return result


def make_recommendations(es, user_info, index, n_articles=10):
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
        articles = sorted(articles, key=lambda k: k['score'], reverse=True)

        recommendations[user] = articles[0:n_articles]
        n_recommended = len(recommendations[user])
        logger.info(
            'User {}: recommended {} articles.'.format(user, n_recommended))
    return recommendations


def recommend(es, api_key, api_url, index):
    """Makes and sends recommendations to all users."""
    total_users = get_user_ids(0, api_key, api_url)['users']['num']
    logger.info(
        'Starting recommending articles for {} users'.format(total_users))
    recommendation_count = 0
    while recommendation_count < total_users:
        user_ids = get_user_ids(0, api_key, api_url)['users']['user_ids']
        user_info = get_user_info(user_ids, api_key, api_url)

        recommendations = make_recommendations(es, user_info, index)

        if recommendations:
            send_recommendations(recommendations, api_key, api_url)
        recommendation_count += len(user_ids)
        logger.info('Processed {} users'.format(recommendation_count))


def run(api_key, api_url, index):
    """Runs the recommender system:
        - Updates index with new articles
        - Fetches user info for all users
        - Creates and sends recommendations for each user
        """
    es = Elasticsearch(hosts=[ELASTICSEARCH_HOST])
    if not es.indices.exists(index=index):
        logger.info('Creating index')
        init_index(es, index)
    logger.info('Indexing articles from arXivDigest API.')
    run_indexing(es, index, api_key, api_url)
    recommend(es, api_key, api_url, index)
    logger.info('\nFinished recommending articles.')


if __name__ == '__main__':
    logger = logging.getLogger(__name__)

    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ],
    )
    logger.setLevel(config_file.get('log_level', logging.INFO))
    run(API_KEY, API_URL, INDEX)
