"""Search functionality using Elasticsearch."""

def search_articles(es, query, page=1, per_page=10):
    """Search articles using Elasticsearch.
    
    Args:
        es: Elasticsearch instance
        query: Search query string
        page: Page number (default: 1)
        per_page: Results per page (default: 10)
    """
    from arxivdigest.core.config import elastic_index_name
    
    from_index = (page - 1) * per_page
    
    result = es.search(
        index=elastic_index_name,
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
