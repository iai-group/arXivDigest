# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

INDEX = 'main_index'

INDEX_SETTINGS = {
    'settings': {
        'index': {
            'number_of_shards': 1,
            'number_of_replicas': 0
        },
    },
    'mappings': {
        'properties': {
            'title': {
                'type': 'text',
                'term_vector': 'with_positions',
                'analyzer': 'english'
            },
            'abstract': {
                'type': 'text',
                'term_vector': 'with_positions',
                'analyzer': 'english'
            },
            'authors': {
                'type': 'nested',
                'properties': {
                    'firstname':  {'type': 'keyword'},
                    'lastname': {'type': 'keyword'},
                    'affiliations': {'type': 'object'}
                },
            },
            'categories': {
                'type': 'object',
            },
            'comments': {
                'type': 'text',
                'term_vector': 'with_positions',
                'analyzer': 'english'
            },
            'doi': {
                'type': 'keyword',
            },
            'journal': {
                'type': 'keyword',
            },
            'license': {
                'type': 'keyword',
            },
            'date': {
                'type': 'date',
                'format': 'date'
            },
            'catch_all': {
                'type': 'text',
                'term_vector': 'with_positions',
                'analyzer': 'english'
            },
        }
    }
}
print('Creating index')
es = Elasticsearch()
es.indices.create(index=INDEX, body=INDEX_SETTINGS)
print('Finished creating index')
