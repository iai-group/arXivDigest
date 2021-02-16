# Scripts

To be scheduled to run regularly on weekdays:

  * `interleave_articles.py`: Interleaves article recommendations.
  * `scrape_arxiv.py`: Downloads new articles from arXiv.
  * `send_digest_mail.py`: Sends out digest email.

To be used for benchmarking:

  * `evaluation.py`: Generates evaluation measures.

To be used once during setup:

  * `init_topic_list.py`: Populates the database with an initial list of topics.

## Semantic Scholar profile suggestions

`gen_semantic_scholar_suggestions.py` can be used to generate Semantic Scholar profile suggestions for the users who
currently do not provide a link to their Semantic Scholar profiles:

```
usage: gen_semantic_scholar_suggestions.py [-h] [--index INDEX] [--hosts HOSTS]

Generate Semantic Scholar profile suggestions for all arXivDigest users whose profiles currently do not contain a link to a profile.

optional arguments:
  -h, --help     show this help message and exit
  --index INDEX  Semantic Scholar Open Research Corpus Elasticsearch index name (default: open_research)
  --hosts HOSTS  Elasticsearch hosts (default: ['http://127.0.0.1:9200'])
```

The generated suggestions will be shown to the users in a modal upon login.

`gen_semantic_scholar_suggestions.py` relies on Elasticsearch and the 
[Semantic Scholar Open Research Corpus](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/). The next
section will provide instructions on how to index this dataset in Elasticsearch.

### Indexing the Semantic Scholar Open Research Corpus in Elasticsearch

Before starting, make sure that the dataset (or parts of it) is downloaded and available in 
`data/open_research_corpus/`. For this, you can either execute  `download_open_research_corpus.sh` or follow the download
instructions [here](http://s2-public-api-prod.us-west-2.elasticbeanstalk.com/corpus/download/). Proceed to run
`index_open_research_corpus.py`:
```
usage: index_open_research_corpus.py [-h] [--index INDEX] [--hosts HOSTS]

Index the Semantic Scholar Open Research Corpus in Elasticsearch.

optional arguments:
  -h, --help     show this help message and exit
  --index INDEX  Elasticsearch index name (default: open_research)
  --hosts HOSTS  Elasticsearch hosts (default: ['http://127.0.0.1:9200'])
```

`gen_semantic_scholar_suggestions.py` utilizes only the author field of the articles in the dataset to generate profile 
suggestions. For this reason, and in order to save space, `index_open_research_corpus.py` creates an Elasticsearch index
of the dataset that contains only the author field of the articles.