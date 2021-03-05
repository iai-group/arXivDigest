from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from pathlib import Path
import json
import gzip
import argparse


def gen_corpus(index: str, path: Path):
    for file_path in path.glob("s2-corpus-*.gz"):
        with gzip.open(file_path, "r") as file:
            for line in file:
                article = json.loads(line)
                yield {
                    "_index": index,
                    "_id": article.pop("id"),
                    "_source": {
                        "title": article["title"],
                        "authors": article["authors"],
                        "paperAbstract": article["paperAbstract"],
                        "year": article["year"],
                        "fieldsOfStudy": article["fieldsOfStudy"],
                        "venue": article["venue"],
                        "journalName": article["journalName"],
                        "journalVolume": article["journalVolume"],
                        "journalPages": article["journalPages"],
                    },
                }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Index the Semantic Scholar Open Research Corpus in Elasticsearch.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--index", type=str, help="Elasticsearch index name", default="open_research"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Elasticsearch host",
        default="http://127.0.0.1:9200",
    )
    parser.add_argument(
        "--path",
        type=Path,
        help="path to directory containing the dataset (.gz files)",
        default=Path(__file__).parent / "data" / "open_research_corpus",
    )
    args = parser.parse_args()

    es = Elasticsearch(hosts=[args.host])
    if not es.indices.exists(args.index):
        es.indices.create(args.index)

    bulk(
        es,
        gen_corpus(args.index, args.path),
        chunk_size=1000,
        max_retries=10,
    )
