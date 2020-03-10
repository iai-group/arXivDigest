# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, 2020, The arXivDigest project

from urllib import request
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def get_article_ids(api_key, api_url, date):
    """Get a list of the article_ids from the arXivDigest API for the date object supplied, defaults to the current date."""
    url = '{}articles'.format(api_url)
    url = url + '?date=' + date.strftime("%Y-%m-%d") if date else url
    req = request.Request(url, headers={'api_key': api_key})
    resp = request.urlopen(req)
    return json.loads(resp.read())


def get_article_data(api_key, api_url, article_ids, batch_size=100):
    """Return a nested dictionary of data about the supplied article_ids,
     by querying the arXivDigest API for the article data.
     Batch_size is the limit of number of articles to retrieve data for in one request."""
    article_data = {}
    for i in range(0, len(article_ids), batch_size):
        id_batch = ','.join(article_ids[i:i + batch_size])
        req = request.Request('{}articledata?article_id={}'.format(api_url, id_batch),
                              headers={'api_key': api_key})

        resp = request.urlopen(req)
        article_data.update(json.loads(resp.read())['articles'])

    for article_id, article in article_data.items():
        article_data[article_id]['catch_all'] = article['title'] + " " + article['abstract']
    return article_data


def bulk_insert_articles(index, article_data):
    """Bulk insert article data into the elastic search index."""
    es = Elasticsearch()
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


def run_indexing(index, api_key, api_url, date=None):
    """Indexes article data for new additions to the arXivDigest database for the given date object, defaults to the current date."""
    print('Retrieving article IDs')
    article_ids = get_article_ids(api_key, api_url, date)['articles']['article_ids']
    print('Retriving article data')
    article_data = get_article_data(api_key, api_url, article_ids)
    print('Starting bulk insertion of article data into index')
    bulk_insert_articles(index, article_data)
    print('Bulk insertion complete')
