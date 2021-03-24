# Scripts

This directory contains three types of scripts:
* one-time setup scripts;
* regular scripts meant to be run on weekdays; and
* manual scripts.


## One-time setup scripts

* `init_topic_list.py`: Populates the database with an initial list of topics.

## Regular scripts

* `interleave_articles.py`: Interleaves article recommendations.
* `scrape_arxiv.py`: Downloads new articles from arXiv.
* `send_digest_mail.py`: Sends out digest email.

## Manual scripts

* `evaluation.py`: Generates evaluation measures.
* `gen_semantic_scholar_suggestions.py`: Generates Semantic Scholar profile suggestions.
* `index_open_research_corpus.py`: Indexes the Semantic Scholar Open Research Corpus in Elasticsearch.
* `download_open_research_corpus.sh`: Downloads the Semantic Scholar Open Research Corpus.

### Semantic Scholar profile suggestions

`gen_semantic_scholar_suggestions.py` can be used to generate Semantic Scholar profile suggestions for the users who
currently do not provide a link to their Semantic Scholar profiles:

```
usage: gen_semantic_scholar_suggestions.py [-h] [--index INDEX] [--host HOST] [--method {score,frequency}] [--batch-size BATCH_SIZE] [--max-suggestions MAX_SUGGESTIONS] [-k K] [--max-edit-distance MAX_EDIT_DISTANCE] [--output OUTPUT]

Generate Semantic Scholar profile suggestions for all arXivDigest users whose profiles currently do not contain a link to a profile.

optional arguments:
  -h, --help            show this help message and exit
  --index INDEX         Semantic Scholar Open Research Corpus Elasticsearch index name (default: open_research)
  --host HOST           Elasticsearch host (default: http://127.0.0.1:9200)
  --method {score,frequency}
                        profile matching method (default: score)
  --batch-size BATCH_SIZE
                        user batch size (suggestions are generated in batches of users) (default: 500)
  --max-suggestions MAX_SUGGESTIONS
                        max number of suggestions per user (default: 5)
  -k K                  number of top Elasticsearch query results (top-k) to take into consideration when finding profile candidates for a user (default: 50)
  --max-edit-distance MAX_EDIT_DISTANCE
                        max edit distance between a user's name and a suggestion (default: 1)
  --output OUTPUT       if provided, suggestions are not stored in the database, but are instead written to this path in a TREC suggestion format (suggestions are also generated for all users) (default: None)
```

The generated suggestions will be shown to the users in a modal upon login.

`gen_semantic_scholar_suggestions.py` relies on Elasticsearch and the 
[Semantic Scholar Open Research Corpus](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/). The next
section provides instructions on how to index this dataset in Elasticsearch.

#### Indexing the Semantic Scholar Open Research Corpus in Elasticsearch

Before starting, make sure that the dataset (or parts of it) is downloaded. For this, you can either execute 
`download_open_research_corpus.sh` or follow the download instructions
[here](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/). Proceed to run
`index_open_research_corpus.py`:
```
usage: index_open_research_corpus.py [-h] [--index INDEX] [--host HOST] [--path PATH]

Index the Semantic Scholar Open Research Corpus in Elasticsearch.

optional arguments:
  -h, --help     show this help message and exit
  --index INDEX  Elasticsearch index name (default: open_research)
  --host HOST    Elasticsearch host (default: http://127.0.0.1:9200)
  --path PATH    path to directory containing the dataset (.gz files) (default: data/open_research_corpus)
```
