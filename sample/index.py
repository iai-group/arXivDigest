# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from pprint import pprint
from urllib import request, parse, error
import json
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

API_KEY = '4c02e337-c94b-48b6-b30e-0c06839c81e6'
URL = 'http://127.0.0.1:5000/'
INDEX = 'main_index'


def articles(api_key):
    '''Get a list of the article_ids that can be ranked this day from the ArXivDigest API.'''
    req = request.Request('{}articles'.format(URL),
                          headers={'api_key': api_key})
    try:
        resp = request.urlopen(req)
    except error.HTTPError as e:
        print(e.read())
    return json.loads(resp.read())


def article_data(api_key, article_ids, batch_size=100):
    '''Return a nested dictionary of data about the supplied article_ids,
     by querying the ArXivDigest API for the article data. 
     Batch_size is the limit of number of articles to retrieve data for in one request.'''
    article_data = {}
    for i in range(0, len(article_ids), batch_size):
        id_batch = ','.join(article_ids[i:i+batch_size])
        req = request.Request('{}articledata?article_id={}'.format(URL, id_batch),
                              headers={'api_key': api_key})
        try:
            resp = request.urlopen(req)
        except error.HTTPError as e:
            print(e.read())
        article_data.update(json.loads(resp.read())['articles'])
    return article_data


def bulk_insert_articles(index, article_data):
    '''Bulk insert article data into the elastic search index.'''
    bulk_docs = []
    for article_id, article_fields in data.items():
        doc = {
            '_index': index,
            '_type': '_doc',
            '_id': article_id,
            '_source': article_fields
        }
        bulk_docs.append(doc)
    bulk(es, bulk_docs, request_timeout=10)


print('Retrieving article IDs')
article_ids = articles(API_KEY)['articles']['article_ids']
print('Retriving article data')
article_data = article_data(API_KEY, article_ids)
print('Starting bulk insertion into index')
es = Elasticsearch()
bulk_insert_articles(INDEX, article_data)
print('Bulk insertion complete')
