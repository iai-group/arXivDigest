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


def fetch_articles(db_config, since_date=None, limit=None, offset=None):
    """Fetch articles from database, optionally filtering by date
    
    Args:
        db_config: Database configuration dict
        since_date: Only fetch articles after this date (for incremental indexing)
        limit: Maximum number of articles to fetch
        offset: Number of articles to skip (for batch processing)
    """
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
    
    if offset:
        query += " OFFSET %s"
        params.append(offset)
    
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
    
    # Load index settings from config file
    settings_path = Path(__file__).parent.parent / 'config' / 'index_settings.json'
    with open(settings_path) as f:
        index_settings = json.load(f)
    
    es.indices.create(index=index, body=index_settings)
    logger.info(f"Created index: {index}")


def index_articles(mode='incremental', index=None, es_url=None, db_config=None, limit=None, offset=None, progress_file=None):
    """Index articles from database to Elasticsearch
    
    Args:
        mode: 'full', 'incremental', or 'test'
        index: Elasticsearch index name
        es_url: Elasticsearch URL
        db_config: Database configuration dict
        limit: Maximum number of articles to index (batch size)
        offset: Number of articles to skip (for batch processing)
        progress_file: File to write progress updates to
    """
    from arxivdigest.core.config import config_elasticsearch, config_sql, elastic_index_name
    
    def update_progress(message, current=None, total=None):
        """Update progress to both logger and progress file"""
        if current is not None and total is not None:
            pct = (current / total * 100) if total > 0 else 0
            full_msg = f"{message} [{current}/{total}] ({pct:.1f}%)"
        else:
            full_msg = message
        logger.info(full_msg)
        if progress_file:
            with open(progress_file, 'w') as f:
                f.write(full_msg + '\n')
    
    if not es_url:
        es_url = config_elasticsearch.get('url', 'http://localhost:9200')
    if not index:
        index = elastic_index_name
    if not db_config:
        db_config = config_sql
    
    es = Elasticsearch(hosts=[es_url])
    
    # Create index if needed
    update_progress("Creating index if needed...")
    create_index_if_not_exists(es, index)
    
    # Determine date filter
    since_date = None
    if mode == 'incremental':
        since_date = get_latest_article_date(es, index)
        if since_date:
            update_progress(f"Incremental mode: indexing articles after {since_date}")
        else:
            update_progress("No existing articles found, performing full index")
    elif mode == 'test':
        update_progress(f"Test mode: indexing up to {limit} articles")
    else:
        if offset and limit:
            update_progress(f"Batch mode: indexing articles {offset} to {offset + limit}")
        elif offset:
            update_progress(f"Full reindex mode: starting from offset {offset}")
        elif limit:
            update_progress(f"Full reindex mode: indexing up to {limit} articles")
        else:
            update_progress("Full reindex mode: indexing all articles")
    
    # Fetch articles
    update_progress("Fetching articles from database...")
    articles = fetch_articles(db_config, since_date, limit, offset)
    
    if not articles:
        update_progress("No new articles to index. Done!")
        return
    
    total_articles = len(articles)
    update_progress(f"Found {total_articles} articles to index")
    
    # Fetch related data
    update_progress("Fetching authors...")
    article_ids = [a['article_id'] for a in articles]
    authors = fetch_article_authors(db_config, article_ids)
    
    update_progress("Fetching categories...")
    categories = fetch_article_categories(db_config, article_ids)
    
    # Bulk index with progress tracking
    update_progress("Starting bulk indexing...", 0, total_articles)
    
    indexed_count = 0
    failed_count = 0
    chunk_size = 500
    
    # Process in chunks to show progress
    for i in range(0, len(articles), chunk_size):
        chunk = articles[i:i + chunk_size]
        chunk_ids = [a['article_id'] for a in chunk]
        chunk_authors = {k: v for k, v in authors.items() if k in chunk_ids}
        chunk_categories = {k: v for k, v in categories.items() if k in chunk_ids}
        
        actions = list(generate_bulk_actions(chunk, chunk_authors, chunk_categories, index))
        success, failed = bulk(es, actions, chunk_size=chunk_size, raise_on_error=False)
        
        indexed_count += success
        if failed:
            failed_count += len(failed)
        
        update_progress("Indexing articles", indexed_count, total_articles)
    
    update_progress(f"COMPLETE: Indexed {indexed_count} articles successfully. Failed: {failed_count}")


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
        default=None,
        help='Maximum number of articles to index (batch size). Required for test mode.'
    )
    parser.add_argument(
        '--offset',
        type=int,
        default=None,
        help='Number of articles to skip (for batch processing). Use with --limit for manual batching.'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=None,
        dest='batch_size',
        help='Alias for --limit (batch size for processing)'
    )
    parser.add_argument(
        '--index',
        help='Elasticsearch index name (overrides config.json)'
    )
    parser.add_argument(
        '--es-url',
        help='Elasticsearch URL (overrides config.json)'
    )
    parser.add_argument(
        '--progress-file',
        default='/tmp/index_progress.txt',
        help='File to write progress updates to (for background monitoring)'
    )
    
    args = parser.parse_args()
    
    # Determine limit: use batch_size if provided, otherwise use limit
    limit = args.batch_size or args.limit
    
    # For test mode, default to 10000 if no limit specified
    if args.mode == 'test' and limit is None:
        limit = 10000
    
    index_articles(
        mode=args.mode,
        index=args.index,
        es_url=args.es_url,
        limit=limit,
        offset=args.offset,
        progress_file=args.progress_file
    )
