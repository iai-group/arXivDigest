#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Index articles to Elasticsearch for search functionality."""

import mysql.connector
from elasticsearch import Elasticsearch

DB_CONFIG = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'arxivdigest'
}

USER_ID = 624

def index_articles():
    """Index articles for user's topics to Elasticsearch."""
    
    # Connect to MySQL
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)
    
    # Get user's topics
    cur.execute("""
        SELECT t.topic 
        FROM user_topics ut 
        JOIN topics t ON ut.topic_id = t.topic_id 
        WHERE ut.user_id = %s 
        AND ut.state IN ('USER_ADDED', 'SYSTEM_RECOMMENDED_ACCEPTED')
    """, (USER_ID,))
    
    topics = [row['topic'] for row in cur.fetchall()]
    print(f"Found {len(topics)} topics for user")
    
    # Get articles (limit 10000)
    cur.execute("""
        SELECT article_id, title, abstract, datestamp
        FROM articles
        ORDER BY datestamp DESC
        LIMIT 10000
    """)
    
    articles = cur.fetchall()
    print(f"Found {len(articles)} articles to index")
    
    cur.close()
    conn.close()
    
    # Connect to Elasticsearch
    es = Elasticsearch(['http://localhost:9200'])
    
    # Create index if not exists
    index_name = 'arxiv_articles'
    if not es.indices.exists(index=index_name):
        es.indices.create(index=index_name, body={
            'mappings': {
                'properties': {
                    'article_id': {'type': 'keyword'},
                    'title': {'type': 'text'},
                    'abstract': {'type': 'text'},
                    'authors': {'type': 'text'},
                    'categories': {'type': 'keyword'},
                    'datestamp': {'type': 'date'}
                }
            }
        })
        print(f"Created index: {index_name}")
    
    # Index articles
    for i, article in enumerate(articles):
        es.index(index=index_name, id=article['article_id'], document={
            'article_id': article['article_id'],
            'title': article['title'],
            'abstract': article['abstract'],
            'datestamp': article['datestamp'].isoformat() if article['datestamp'] else None
        })
        
        if (i + 1) % 1000 == 0:
            print(f"Indexed {i + 1} articles...")
    
    print(f"✓ Successfully indexed {len(articles)} articles")

if __name__ == '__main__':
    index_articles()
