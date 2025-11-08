#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import json
import logging
import sys
from pathlib import Path

import mysql.connector
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent.parent / 'config.json'
    with open(config_path) as f:
        return json.load(f)


def get_latest_article_date(es, index):
    """Get the latest article date from Elasticsearch index"""
    if not es.indices.exists(index=index):
        return None
    
    query = {
        'size': 1,
        'sort': [{'date': {'order': 'desc'}}],
        '_source': ['date']
    }
    
    try:
        result = es.search(index=index, body=query)
        if result['hits']['hits']:
            return result['hits']['hits'][0]['_source']['date']
    except Exception as e:
        logger.warning(f"Could not get latest article date: {e}")
    
    return None


def fetch_articles(db_config, since_date=None, limit=None):
    """Fetch articles from database, optionally filtering by date"""
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    query = """
        SELECT 
            a.article_id, a.title, a.abstract, a.doi, 
            a.comments, a.license, a.journal, a.datestamp
        FROM articles a
        WHERE a.datestamp IS NOT NULL
    """
    
    params = []
    if since_date:
        query += " AND a.datestamp > %s"
        params.append(since_date)
    
    query += " ORDER BY a.datestamp"
    
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    
    cursor.execute(query, params)
    articles = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return articles


def fetch_article_authors(db_config, article_ids):
    """Fetch authors and affiliations for given article IDs"""
    if not article_ids:
        return {}
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    placeholders = ','.join(['%s'] * len(article_ids))
    query = f"""
        SELECT 
            aa.article_id, aa.firstname, aa.lastname, aa.author_id
        FROM article_authors aa
        WHERE aa.article_id IN ({placeholders})
        ORDER BY aa.article_id, aa.author_id
    """
    
    cursor.execute(query, article_ids)
    authors_data = cursor.fetchall()
    
    # Fetch affiliations
    author_ids = [a['author_id'] for a in authors_data]
    affiliations = {}
    
    if author_ids:
        aff_placeholders = ','.join(['%s'] * len(author_ids))
        aff_query = f"""
            SELECT author_id, affiliation
            FROM author_affiliations
            WHERE author_id IN ({aff_placeholders})
        """
        cursor.execute(aff_query, author_ids)
        for row in cursor.fetchall():
            if row['author_id'] not in affiliations:
                affiliations[row['author_id']] = []
            affiliations[row['author_id']].append(row['affiliation'])
    
    cursor.close()
    conn.close()
    
    # Group by article
    authors_by_article = {}
    for author in authors_data:
        article_id = author['article_id']
        if article_id not in authors_by_article:
            authors_by_article[article_id] = []
        
        authors_by_article[article_id].append({
            'firstname': author['firstname'] or '',
            'lastname': author['lastname'],
            'affiliations': affiliations.get(author['author_id'], [])
        })
    
    return authors_by_article


def fetch_article_categories(db_config, article_ids):
    """Fetch categories for given article IDs"""
    if not article_ids:
        return {}
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    placeholders = ','.join(['%s'] * len(article_ids))
    query = f"""
        SELECT ac.article_id, ac.category_id
        FROM article_categories ac
        WHERE ac.article_id IN ({placeholders})
    """
    
    cursor.execute(query, article_ids)
    categories_data = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Group by article
    categories_by_article = {}
    for row in categories_data:
        article_id = row['article_id']
        if article_id not in categories_by_article:
            categories_by_article[article_id] = []
        categories_by_article[article_id].append(row['category_id'])
    
    return categories_by_article


def generate_bulk_actions(articles, authors, categories, index):
    """Generate bulk actions for Elasticsearch"""
    for article in articles:
        article_id = article['article_id']
        
        source = {
            'title': article['title'],
            'abstract': article['abstract'],
            'authors': authors.get(article_id, []),
            'categories': categories.get(article_id, []),
            'doi': article['doi'],
            'comments': article['comments'],
            'license': article['license'],
            'journal': article['journal'],
            'date': article['datestamp'].strftime('%Y-%m-%d') if article['datestamp'] else None,
            'catch_all': article['title'] + ' ' + article['abstract']
        }
        
        yield {
            '_index': index,
            '_id': article_id,
            '_source': source
        }


def create_index_if_not_exists(es, index):
    """Create index with proper mappings if it doesn't exist"""
    if es.indices.exists(index=index):
        return
    
    index_settings = {
        'settings': {
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 0
            }
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
                    }
                },
                'categories': {'type': 'keyword'},
                'comments': {
                    'type': 'text',
                    'term_vector': 'with_positions',
                    'analyzer': 'english'
                },
                'doi': {'type': 'keyword'},
                'journal': {'type': 'keyword'},
                'license': {'type': 'keyword'},
                'date': {
                    'type': 'date',
                    'format': 'date'
                },
                'catch_all': {
                    'type': 'text',
                    'term_vector': 'with_positions',
                    'analyzer': 'english'
                }
            }
        }
    }
    
    es.indices.create(index=index, body=index_settings)
    logger.info(f"Created index: {index}")


def index_articles(mode='incremental', index=None, es_url=None, db_config=None, limit=None):
    """Index articles from database to Elasticsearch"""
    config = load_config()
    
    if not es_url:
        es_url = config['elasticsearch_config']['url']
    if not index:
        index = config['elasticsearch_config'].get('index', 'arxiv')
    if not db_config:
        db_config = config['sql_config']
    
    es = Elasticsearch(hosts=[es_url])
    
    # Create index if needed
    create_index_if_not_exists(es, index)
    
    # Determine date filter
    since_date = None
    if mode == 'incremental':
        since_date = get_latest_article_date(es, index)
        if since_date:
            logger.info(f"Incremental mode: indexing articles after {since_date}")
        else:
            logger.info("No existing articles found, performing full index")
    elif mode == 'test':
        logger.info(f"Test mode: indexing up to {limit} articles")
    else:
        logger.info("Full reindex mode: indexing all articles")
    
    # Fetch articles
    articles = fetch_articles(db_config, since_date, limit)
    
    if not articles:
        logger.info("No new articles to index")
        return
    
    logger.info(f"Found {len(articles)} articles to index")
    
    # Fetch related data
    article_ids = [a['article_id'] for a in articles]
    authors = fetch_article_authors(db_config, article_ids)
    categories = fetch_article_categories(db_config, article_ids)
    
    # Bulk index
    actions = generate_bulk_actions(articles, authors, categories, index)
    success, failed = bulk(es, actions, chunk_size=500, raise_on_error=False)
    
    logger.info(f"Indexed {success} articles successfully")
    if failed:
        logger.warning(f"Failed to index {len(failed)} articles")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Index arXiv articles from database to Elasticsearch',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental', 'test'],
        default='incremental',
        help='Indexing mode: full (reindex all), incremental (only new articles), or test (limited docs)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10000,
        help='Limit number of articles (used with test mode)'
    )
    parser.add_argument(
        '--index',
        help='Elasticsearch index name (overrides config.json)'
    )
    parser.add_argument(
        '--es-url',
        help='Elasticsearch URL (overrides config.json)'
    )
    
    args = parser.parse_args()
    
    limit = args.limit if args.mode == 'test' else None
    
    index_articles(
        mode=args.mode,
        index=args.index,
        es_url=args.es_url,
        limit=limit
    )
