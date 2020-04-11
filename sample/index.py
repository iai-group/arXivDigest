# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, 2020, The arXivDigest project'

from elasticsearch.helpers import bulk


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


def run_indexing(es, index, arxivdigest_connector):
    """Indexes article data for new additions to the arXivDigest
     database for the given date object, defaults to the current date."""
    article_ids = arxivdigest_connector.get_article_ids()
    article_data = arxivdigest_connector.get_article_data(article_ids)
    for article_id, article in article_data.items():
        catch_all = article['title'] + article['abstract']
        article_data[article_id]['catch_all'] = catch_all
    bulk_insert_articles(es, index, article_data)
