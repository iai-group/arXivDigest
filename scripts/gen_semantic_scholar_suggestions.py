from elasticsearch import Elasticsearch
from collections import Counter
import argparse

from arxivdigest.core.database import users_db, semantic_scholar_suggestions_db as s2_db


def author_id_lookup(es: Elasticsearch, name: str, index: str, k=10):
    """
    Find candidate Semantic Scholar author IDs for an author based on their name.

    The IDs are found by: (1) searching for the author in the Semantic Scholar Open Research Corpus, (2) ranking the
    author IDs based on their frequency of occurrence among the top-k results.
    :param es: Elasticsearch instance.
    :param name: Author name.
    :param index: Elasticsearch index.
    :param k: Number of top papers to consider when searching.
    :return: List of tuples (author ID, name) sorted by frequency of occurrence in the search results.
    """
    query = {
        "query": {
            "match": {
                "authors.name": {
                    "query": name,
                    "operator": "and",

                }
            }
        },
        "_source": "authors"
    }
    results = es.search(index=index, body=query, size=k)["hits"]["hits"]
    authors = []
    for article in results:
        for author in article["_source"]["authors"]:
            for author_id in author["ids"]:
                authors.append((author_id, author["name"]))
    id_counts = Counter(author_id for author_id, name in authors)

    return {
        author_id: {
            "name": name,
            "score": id_counts[author_id]
        }
        for author_id, name in authors[:5] if id_counts[author_id] > 1
    }


def gen_suggestions(es: Elasticsearch, index: str):
    number_of_users = users_db.get_number_of_users()
    offset = 0
    while offset < number_of_users:
        users = users_db.get_users_without_semantic_scholar(100, offset)
        suggestions = {user_id: author_id_lookup(es, f"{user_data['firstname']} {user_data['lastname']}", index)
                       for user_id, user_data in users.items()}
        s2_db.update_semantic_scholar_suggestions(suggestions)
        offset += 100


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Semantic Scholar profile suggestions for all arXivDigest "
                                                 "users whose profiles currently do not contain a link to a "
                                                 "profile.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--index", type=str, help="Semantic Scholar Open Research Corpus Elasticsearch index name",
                        default="open_research")
    parser.add_argument("--hosts", type=list, help="Elasticsearch hosts", default=["http://127.0.0.1:9200"])
    args = parser.parse_args()

    es = Elasticsearch(hosts=args.hosts)
    gen_suggestions(es, index=args.index)
