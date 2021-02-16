from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk
from pathlib import Path
import json
import gzip
import argparse


def gen_corpus(index: str):
    for file_path in (Path(__file__).parent / "data" / "open_research_corpus").glob("s2-corpus-*.gz"):
        with gzip.open(file_path, "r") as file:
            for line in file:
                article = json.loads(line)
                yield {
                    "_index": index,
                    "_id": article.pop("id"),
                    "_source": {
                        "authors": article["authors"]
                    }
                }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Index the Semantic Scholar Open Research Corpus in Elasticsearch.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--index", type=str, help="Elasticsearch index name", default="open_research")
    parser.add_argument("--hosts", type=list, help="Elasticsearch hosts", default=["http://127.0.0.1:9200"])
    args = parser.parse_args()

    es = Elasticsearch(hosts=args.hosts)
    if not es.indices.exists(args.index):
        es.indices.create(args.index)

    for success, info in parallel_bulk(es, gen_corpus(args.index)):
        if not success:
            print("Failed to index:", info)
