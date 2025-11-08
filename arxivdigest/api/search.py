"""Search functionality using Elasticsearch."""

def search_articles(es, query, page=1, per_page=10):
    """Search articles using Elasticsearch.
    
    Args:
        es: Elasticsearch instance
        query: Search query string
        page: Page number (default: 1)
        per_page: Results per page (default: 10)
    """
    from_index = (page - 1) * per_page
    
    # Get index from config
    import json
    import os
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.json')
    with open(config_path) as f:
        config = json.load(f)
    index = config.get('elasticsearch_config', {}).get('index', 'arxiv')
    
    result = es.search(
        index=index,
        body={
            'from': from_index,
            'size': per_page,
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^2', 'abstract', 'catch_all']
                }
            }
        }
    )
    
    articles = []
    for hit in result['hits']['hits']:
        articles.append({
            'article_id': hit['_id'],
            'title': hit['_source']['title'],
            'abstract': hit['_source']['abstract'],
            'datestamp': hit['_source'].get('date'),
            'score': hit['_score']
        })
    
    return {
        'articles': articles,
        'total': result['hits']['total']['value'],
        'page': page,
        'per_page': per_page
    }
