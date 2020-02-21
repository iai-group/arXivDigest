import requests
import json

semantic_scholar ='https://api.semanticscholar.org/v1/paper/arXiv:'

def get_article(article_id):
    resp = requests.get(semantic_scholar+article_id)
    article = json.loads(resp.content)

    paperid = article['paperId']
    references = {}
    for reference in article['references']:
        references[reference['paperId']] = reference['title']
    topics = {}
    for topic in article['topics']:
        topics[topic['topicId']] = topic['topic']
    authors = {}
    for author in article['authors']:
        authors[author['authorId']] = author['name']
    venue = article['venue']

    return {
        'paper_id': paperid,
        'references': references,
        'topics': topics,
        'authors': authors,
        'venue': venue
    }

info = get_article('1409.0668')
print(info)