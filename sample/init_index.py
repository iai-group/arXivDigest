# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project

from elasticsearch import Elasticsearch

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
                    'firstname': {'type': 'keyword'},
                    'lastname': {'type': 'keyword'},
                    'affiliations': {'type': 'keyword'}
                },
            },
            'categories': {
                'type': 'keyword',
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


def init_index(index):
    print('Creating index')
    es = Elasticsearch()
    es.indices.create(index=index, body=INDEX_SETTINGS)
    print('Finished creating index')
