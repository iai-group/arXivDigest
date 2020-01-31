from urllib import request
import json
from elasticsearch import Elasticsearch
from collections import defaultdict
from init_index import init_index
from index import run_indexing

API_KEY = '4c02e337-c94b-48b6-b30e-0c06839c81e6'
API_URL = 'http://127.0.0.1:5000/'
INDEX = 'main_index'


def get_user_ids(start, api_key, api_url):
    """Queries the arXivDigest API for user ids starting from 'start'. """
    req = request.Request('%susers?from=%d' % (api_url, start),
                          headers={"api_key": api_key})
    resp = request.urlopen(req)
    return json.loads(resp.read())


def get_user_info(user_ids, api_key, api_url, batch_size=100):
    """Queries the arXivDigest API for userdata for the given 'user_ids'."""
    user_info = {}
    for i in range(0, len(user_ids), batch_size):
        user_id_string = ','.join([str(u) for u in user_ids[i:i + batch_size]])
        url = '%suserinfo?user_id=%s' % (api_url, user_id_string)
        req = request.Request(url, headers={"api_key": api_key})
        resp = request.urlopen(req)
        user_info.update(json.loads(resp.read())['userinfo'])
    return user_info


def get_articles_by_keyword(keyword, index, window_size=1, size=10000):
    """Retrieves articles from the Elasticsearch index mentioning 'keywords',
    the 'window_size' is the number of days back in time articles will
    be included from."""
    es = Elasticsearch()
    query = {
        'query': {
            'bool': {
                'must': {
                    'match': {
                        'catch_all': {
                            'query': keyword,
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
        req = request.Request(api_url + "recommendation", data=data, headers={
            'Content-Type': 'application/json', "api_key": api_key})
        request.urlopen(req)


def make_user_recommendation(keywords, index):
    """Makes recommendations based on list of keywords and returns a list of
    articles. The score of each article is calculated as the sum of the score of
    each keyword, and the explanation is contains all keywords that matched an
    article."""
    article_scores = defaultdict(list)
    article_keywords = defaultdict(list)
    for keyword in keywords:
        for article in get_articles_by_keyword(keyword, index)['hits']['hits']:
            article_scores[article['_id']].append(article['_score'])
            article_keywords[article['_id']].append(keyword)

    result = []
    for article_id in article_scores:
        expl_str = ', '.join(article_keywords[article_id])
        explanation = 'This article matches the keywords: {}'.format(expl_str)
        result.append({'article_id': article_id,
                       'score': sum(article_scores[article_id]),
                       'explanation': explanation
                       })
    return result


def make_recommendations(user_info, index, n_articles=10):
    """Makes recommendations for all the users in user_info based on the
    keywords in user_info. Searches the elasticsearch index for candidates
    and uses the Elasticsearch score as score.
    'n_articles' is the number of articles to recommend for each user."""
    recommendations = {}
    for user, info in user_info.items():
        articles = make_user_recommendation(info['keywords'], index)
        articles = sorted(articles, key=lambda k: k['score'], reverse=True)
        recommendations[user] = articles[0:n_articles]
    return recommendations


def recommend(api_key, api_url, index):
    """Makes and sends recommendations to all users."""
    total_users = get_user_ids(0, api_key, api_url)['users']['num']
    print('Starting recommending articles for {} users'.format(total_users))
    recommendation_count = 0
    while recommendation_count < total_users:
        user_ids = get_user_ids(0, api_key, api_url)['users']['user_ids']
        user_info = get_user_info(user_ids, api_key, api_url)
        recommendations = make_recommendations(user_info, index)
        send_recommendations(recommendations, api_key, api_url)

        recommendation_count += len(user_ids)
        print('\rRecommended articles for {} users'
              .format(recommendation_count), end='')


def run(api_key, api_url, index):
    """Runs the recommender system:
        - Updates index with new articles
        - Fetches user info for all users
        - Creates and sends recommendations for each user
        """
    es = Elasticsearch()
    if not es.indices.exists(index=index):
        init_index(index)
    run_indexing(index, api_key, api_url)
    recommend(api_key, api_url, index)
    print('\nFinished recommending articles')


if __name__ == '__main__':
    run(API_KEY, API_URL, INDEX)
