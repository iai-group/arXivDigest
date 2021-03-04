from elasticsearch import Elasticsearch
from datetime import datetime
from collections import defaultdict
import argparse

from arxivdigest.core.database import users_db, semantic_scholar_suggestions_db as s2_db


def find_author_candidates_by_frequency(
    es: Elasticsearch, index: str, user: dict, max_candidates: int, k: int
) -> dict:
    """
    Find candidate Semantic Scholar author IDs for a user. Candidates are found by:
        1. Querying the S2ORC Elasticsearch index for the user's name.
        2. Ranking the authors present in the query results based on their frequency of occurrence.

    :param es: Elasticsearch instance.
    :param user: User.
    :param index: S2ORC Elasticsearch index name.
    :param max_candidates: Max number of candidates returned.
    :param k: Number of top Elasticsearch query results to take into consideration.
    :return: Dictionary {author_id: {name, score}).
    """
    query = {
        "query": {"match": {"authors.name": f"{user['firstname']} {user['lastname']}"}}
    }
    results = es.search(index=index, body=query, size=k)["hits"]["hits"]
    authors = defaultdict(lambda: {"name": "", "count": 0})
    for article in results:
        for author in article["_source"]["authors"]:
            for author_id in author["ids"]:
                authors[author_id]["name"] = " ".join(author["name"].split())
                authors[author_id]["count"] += 1

    return {
        author_id: author_data
        for author_id, author_data in sorted(
            authors.items(), key=lambda a: a[1]["count"], reverse=True
        )[:max_candidates]
    }


def find_author_candidates_by_score(
    es: Elasticsearch, index: str, user: dict, max_candidates: int, k: int
) -> dict:
    """
    Find candidate Semantic Scholar author IDs for a user. Candidates are found by:
        1. Querying the S2ORC Elasticsearch index for the user's name, along with the user's topics of interest.
        2. Ranking the authors present in the query results based on the sum of the scores of the documents they have
        authored.

    :param es: Elasticsearch instance.
    :param user: User.
    :param index: S2ORC Elasticsearch index name.
    :param max_candidates: Max number of candidates returned.
    :param k: Number of top Elasticsearch query results to take into consideration.
    :return: Dictionary {author_id: {name, score}).
    """
    query = {
        "query": {
            "bool": {
                "must": {
                    "match": {"authors.name": f"{user['firstname']} {user['lastname']}"}
                },
                "should": [
                    {
                        "multi_match": {
                            "query": topic["topic"],
                            "fields": ["title", "paperAbstract", "fieldsOfStudy"],
                        }
                    }
                    for topic in user["topics"]
                ],
            },
        }
    }
    results = es.search(index=index, body=query, size=k)["hits"]["hits"]
    authors = defaultdict(lambda: {"name": "", "score": 0})
    for article in results:
        for author in article["_source"]["authors"]:
            for author_id in author["ids"]:
                authors[author_id]["name"] = " ".join(author["name"].split())
                authors[author_id]["score"] += article["_score"]

    return {
        author_id: author_data
        for author_id, author_data in sorted(
            authors.items(), key=lambda a: a[1]["score"], reverse=True
        )[:max_candidates]
    }


def gen_suggestions(
    es: Elasticsearch,
    index: str,
    matching_method: str,
    max_suggestions: int,
    k: int,
    batch_size: int,
):
    """
    Generate suggestions for users in batches.

    :param es: Elasticsearch instance.
    :param index: S2ORC Elasticsearch index name.
    :param matching_method: Profile matching method ("score" or "frequency").
    :param max_suggestions: Max number of suggestions generated per user.
    :param k: Number of top Elasticsearch query results (k-top) to take into consideration when finding profile
    candidates for a user.
    :param batch_size: User batch size.
    """
    timestamp = datetime.now()
    number_of_users = users_db.get_number_of_users_for_suggestion_generation()
    print(
        f"Generating suggestions for {number_of_users} user(s) (timestamp: {timestamp})."
    )

    offset = 0
    while offset < number_of_users:
        users = users_db.get_users_for_suggestion_generation(batch_size, offset)
        suggestions = {
            user_id: PROFILE_MATCHING_METHODS[matching_method](
                es, index, user_data, max_suggestions, k
            )
            for user_id, user_data in users.items()
        }
        s2_db.update_semantic_scholar_suggestions(suggestions, timestamp)
        offset += batch_size


PROFILE_MATCHING_METHODS = {
    "score": find_author_candidates_by_score,
    "frequency": find_author_candidates_by_frequency,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Semantic Scholar profile suggestions for all arXivDigest "
        "users whose profiles currently do not contain a link to a "
        "profile.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--index",
        type=str,
        help="Semantic Scholar Open Research Corpus Elasticsearch index name",
        default="open_research",
    )
    parser.add_argument(
        "--hosts",
        type=list,
        help="Elasticsearch hosts",
        default=["http://127.0.0.1:9200"],
    )
    parser.add_argument(
        "--method",
        help="profile matching method",
        default="score",
        choices=PROFILE_MATCHING_METHODS.keys(),
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="user batch size (suggestions are generated in batches of users)",
        default=500,
    )
    parser.add_argument(
        "--max-suggestions",
        type=int,
        help="max number of suggestions per user",
        default=5,
    )
    parser.add_argument(
        "-k",
        type=int,
        help="number of top Elasticsearch query results (k-top) to take into consideration when finding profile "
        "candidates for a user",
        default=50,
    )
    args = parser.parse_args()

    es = Elasticsearch(hosts=args.hosts)
    gen_suggestions(
        es, args.index, args.method, args.max_suggestions, args.k, args.batch_size
    )
