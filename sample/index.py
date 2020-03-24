# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, 2020, The arXivDigest project'

import json
from urllib import request

from elasticsearch.helpers import bulk


def get_article_ids(api_key, api_url):
    """Get a list of the article_ids from the arXivDigest API for the date object supplied, defaults to the current date."""
    url = '{}articles'.format(api_url)
    req = request.Request(url, headers={'api-key': api_key})
    resp = request.urlopen(req)
    return json.loads(resp.read())


def get_article_data(api_key, api_url, article_ids, batch_size=100):
    """Return a nested dictionary of data about the supplied article_ids,
     by querying the arXivDigest API for the article data.
     Batch_size is the limit of number of articles to retrieve data for in one request."""
    article_data = {}
    for i in range(0, len(article_ids), batch_size):
        id_batch = ','.join(article_ids[i:i + batch_size])
        req = request.Request('{}article_data?article_id={}'
                              .format(api_url, id_batch),
                              headers={'api-key': api_key})

        resp = request.urlopen(req)
        article_data.update(json.loads(resp.read())['articles'])

    for article_id, article in article_data.items():
        catch_all = article['title'] + " " + article['abstract']
        article_data[article_id]['catch_all'] = catch_all
    return article_data


def bulk_insert_articles(es, index, article_data):
    """Bulk insert article data into the elastic search index."""
    bulk_docs = []
    for article_id, article_fields in article_data.items():
        doc = {
            '_index': index,
            '_type': '_doc',
            '_id': article_id,
            '_source': article_fields
        }
        bulk_docs.append(doc)
    bulk(es, bulk_docs, request_timeout=10)


def run_indexing(es, index, api_key, api_url):
    """Indexes article data for new additions to the arXivDigest
     database for the given date object, defaults to the current date."""
    article_ids = get_article_ids(api_key, api_url)['articles']
    article_data = get_article_data(api_key, api_url, article_ids)
    bulk_insert_articles(es, index, article_data)
