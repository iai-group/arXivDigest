from elasticsearch import Elasticsearch
from datetime import datetime
from collections import defaultdict
from functools import reduce
from pathlib import Path
import editdistance
import argparse
import operator

from arxivdigest.core.database import users_db, semantic_scholar_suggestions_db as s2_db


def edit_distance(suggestion: str, user: dict) -> int:
    """
    Calculate the minimum edit distance between a user and a suggestion. The minimum distance between the suggestion
    and the user's name on the following formats is returned:
        1. Full name
        2. First Last
        3. F Last

    :param user: User.
    :param suggestion: Suggestion.
    :return: Min edit distance.
    """

    # Remove punctuation and middle names from the suggestion in case the user's name does not contain middle names.
    clean_suggestion = suggestion.replace(".", "")
    try:
        clean_suggestion = " ".join(
            clean_suggestion.split()[:: len(clean_suggestion.split()) - 1]
        )
    except ValueError:
        # If the suggestion contains only one name (e.g. only last name), attempting to remove middle names will fail
        # with a ValueError as the slice step will be zero.
        pass

    name_formats = {
        f"{user['firstname']} {user['lastname']}",
        f"{user['firstname'].split()[0]} {user['lastname'].split()[-1]}",
        f"{user['firstname'][0]} {user['lastname'].split()[-1]}",
    }
    return min(
        editdistance.eval(
            clean_suggestion,
            name_format,
        )
        for name_format in name_formats
    )


def find_author_candidates_by_frequency(
    es: Elasticsearch,
    index: str,
    user: dict,
    max_candidates: int,
    k: int,
    max_edit_distance: int,
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
    :param max_edit_distance: Max edit distance between user's name and a suggestion.
    :return: Dictionary {author_id: {name, score}).
    """
    print(
        f"Querying for user #{user['user_id']}",
        end="\r",
    )
    query = {
        "query": {"match": {"authors.name": f"{user['firstname']} {user['lastname']}"}}
    }
    results = es.search(index=index, body=query, size=k)["hits"]["hits"]
    authors = defaultdict(lambda: {"name": "", "score": 0})
    for article in results:
        for author in article["_source"]["authors"]:
            for author_id in author["ids"]:
                author_name = " ".join(author["name"].split())
                if edit_distance(author_name, user) > max_edit_distance:
                    continue
                authors[author_id]["name"] = author_name
                authors[author_id]["score"] += 1

    return {
        author_id: author_data
        for author_id, author_data in sorted(
            authors.items(), key=lambda a: a[1]["score"], reverse=True
        )[:max_candidates]
    }


def find_author_candidates_by_score(
    es: Elasticsearch,
    index: str,
    user: dict,
    max_candidates: int,
    k: int,
    max_edit_distance: int,
) -> dict:
    """
    Find candidate Semantic Scholar author IDs for a user. Candidates are found by:
        1. For each of the user's topics of interest, query the S2ORC Elasticsearch index for the user's name
        together with the topic.
        2. Aggregate the results and rank the authors that are present based on the sum of the scores of
        the documents they have authored.

    :param es: Elasticsearch instance.
    :param user: User.
    :param index: S2ORC Elasticsearch index name.
    :param max_candidates: Max number of candidates returned.
    :param k: Number of top Elasticsearch query results to take into consideration.
    :param max_edit_distance: Max edit distance between user's name and a suggestion.
    :return: Dictionary {author_id: {name, score}).
    """

    def search(topic_index: int):
        print(
            f"Querying for user #{user['user_id']} ({len(user['topics'])} topics)"
            f"{'.' * (topic_index + 1)}",
            end="\r",
            flush=True,
        )
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "authors.name": f"{user['firstname']} {user['lastname']}"
                            }
                        },
                        {
                            "multi_match": {
                                "query": user["topics"][topic_index]["topic"],
                                "fields": ["title", "paperAbstract", "fieldsOfStudy"],
                            }
                        },
                    ],
                },
            }
        }
        return es.search(index=index, body=query, size=k)["hits"]["hits"]

    results = reduce(operator.concat, (search(i) for i in range(len(user["topics"]))))
    authors = defaultdict(lambda: {"name": "", "score": 0})
    for article in results:
        for author in article["_source"]["authors"]:
            for author_id in author["ids"]:
                author_name = " ".join(author["name"].split())
                if edit_distance(author_name, user) > max_edit_distance:
                    continue
                authors[author_id]["name"] = author_name
                authors[author_id]["score"] += article["_score"]

    return {
        author_id: author_data
        for author_id, author_data in sorted(
            authors.items(), key=lambda a: a[1]["score"], reverse=True
        )[:max_candidates]
    }


def write_suggestions(suggestions: dict, path: Path, matching_method: str):
    """
    Write suggestions to disk in a TREC suggestion format.

    :param suggestions: Suggestions.
    :param path: Output path.
    :param matching_method: Profile matching method.
    :return:
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as output_file:
        for user_id, user_suggestions in suggestions.items():
            for rank, (suggestion_id, suggestion) in enumerate(
                sorted(
                    user_suggestions.items(),
                    key=lambda s: s[1]["score"],
                    reverse=True,
                ),
                1,
            ):
                output_file.write(
                    f"{user_id} Q0 {suggestion_id} {rank} {suggestion['score']} {matching_method}\n"
                )


def gen_suggestions(
    es: Elasticsearch,
    index: str,
    matching_method: str,
    max_suggestions: int,
    k: int,
    batch_size: int,
    max_edit_distance: int,
    output: Path = None,
):
    """
    Generate suggestions for users in batches.

    :param es: Elasticsearch instance.
    :param index: S2ORC Elasticsearch index name.
    :param matching_method: Profile matching method ("score" or "frequency").
    :param max_suggestions: Max number of suggestions generated per user.
    :param k: Number of top Elasticsearch query results (top-k) to take into consideration when finding profile
    candidates for a user.
    :param batch_size: User batch size.
    :param max_edit_distance: Max edit distance between user's name and a suggestion.
    :param output: If provided, suggestions are not stored in the database, but are instead written to this path in
    a TREC suggestion format. Suggestions are also generated for all users.
    """
    timestamp = datetime.now()
    number_of_users = (
        users_db.get_number_of_users()
        if output
        else users_db.get_number_of_users_for_suggestion_generation()
    )
    print(
        f"Generating suggestions for {number_of_users} user(s) (timestamp: {timestamp})."
    )

    offset = 0
    while offset < number_of_users:
        users = users_db.get_users_for_suggestion_generation(
            batch_size, offset, output is not None
        )
        suggestions = {
            user_id: PROFILE_MATCHING_METHODS[matching_method](
                es, index, user_data, max_suggestions, k, max_edit_distance
            )
            for user_id, user_data in users.items()
        }
        if output:
            write_suggestions(suggestions, output, matching_method)
        else:
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
        "--host",
        type=str,
        help="Elasticsearch host",
        default="http://127.0.0.1:9200",
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
        help="number of top Elasticsearch query results (top-k) to take into consideration when finding profile "
        "candidates for a user",
        default=50,
    )
    parser.add_argument(
        "--max-edit-distance",
        type=int,
        help="max edit distance between a user's name and a suggestion",
        default=1,
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="if provided, suggestions are not stored in the database, but are instead written to this path in a "
        "TREC suggestion format (suggestions are also generated for all users)",
        default=None,
    )
    args = parser.parse_args()

    es = Elasticsearch(hosts=[args.host])
    gen_suggestions(
        es,
        args.index,
        args.method,
        args.max_suggestions,
        args.k,
        args.batch_size,
        args.max_edit_distance,
        args.output,
    )
