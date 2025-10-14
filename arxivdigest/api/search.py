"""Search functionality using Elasticsearch."""

from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

def search_articles(query, page=1, per_page=10):
    """Search articles using Elasticsearch."""
    from_index = (page - 1) * per_page
    
    result = es.search(
        index='arxiv_articles',
        body={
            'from': from_index,
            'size': per_page,
            'query': {
                'multi_match': {
                    'query': query,
                    'fields': ['title^2', 'abstract']
                }
            }
        }
    )
    
    articles = []
    for hit in result['hits']['hits']:
        articles.append({
            'article_id': hit['_source']['article_id'],
            'title': hit['_source']['title'],
            'abstract': hit['_source']['abstract'],
            'datestamp': hit['_source']['datestamp'],
            'score': hit['_score']
        })
    
    return {
        'articles': articles,
        'total': result['hits']['total']['value'],
        'page': page,
        'per_page': per_page
    }
