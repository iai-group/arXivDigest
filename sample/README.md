# Sample System

This folder contains a sample implementation of a baseline recommender system that scores articles based on user topics.


## Overview

The system has several stages of execution:
  * First, it makes sure an Elasticsearch index with the correct mappings exist.  If not it will be created.
  * Then, it queries the arXivDigest API for articles to add to the index.  These are the articles that will serve as candidate recommendations later.
  * Next, the system queries the arXivDigest API for user information.  This is the information that the system bases its personalized recommendations on.
  * The system then creates personalized recommendations for each user.  Specifically, it searches the Elasticsearch index for the best matching articles, using the user's topics as queries.  Then, it aggregates, for each article, the relevance scores of all topics.
  * Finally the articles with the highest overall score for each user are submitted to the arXivDigest API as recommendations.


## Usage

  1. Download and run an [Elasticsearch](https://www.elastic.co/downloads/elasticsearch) server (version 7.5.1 or above).
  2. Download and install the [Python Elasticsearch Client](https://elasticsearch-py.readthedocs.io/en/master/).
  3. Update the constants in [system.py](sample/system.py) such that the system uses the correct API-key and API-url.
  4. Run `python system.py`.

 It is possible to override the default settings of the system by creating a config file in one of the following locations:
   * `~/arxivdigest/system_config.json`
   * `/etc/arxivdigest/system_config.json`
   * `%cwd%/system_config.json`
 
The file should be in JSON format and include the following keys:   
   * `api_url` : Address of the arXivdigest API 
   * `api_key` : An active API key for the arXivDigest API
   * `elasticsearch_host` : Address and port of the Elasticsearch server
   * `index_name` : Name of the index that will be used
   * `log_level` : Level of messages to log accepts: 'FATAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'

Example:

```json
  {
    "api_url": "https://api.arxivdigest.org/",
    "api_key" : "4c02e337-c94b-48b6-b30e-0c06839c81e6",
    "elasticsearch_host": {"host": "127.0.0.1", "port": 9200},
    "index_name": "main_index"
  }
```
