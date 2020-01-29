# Sample System

This folder contains a sample implementation of a recommender system.

## Overview

The system has several stages of execution:
- First makes sure an Elasticsearch index with the correct mappings exist. If not it will be created.
- Then it queries the arXivDigest API for articles to add to the index. These are the articles that will be recommended later.
- Next the system queries the arXivDigest API for user information. This is the information which the system bases its recommendations on.
- For each user the system queries the index for recommendations are made, currently only the user's keywords are used to search the Elastic search index for the best matching articles. 
- Finally the articles found for each user are submitted to the arXivDigest API as recommendations. 

## Usage

Before running the system make sure that an Elasticsearch server is running and to configure the needed settings. 
API url, Elasticsearch url and index name can be configured at the top of system.py.

The system can by run by the command: ``python system.py``
    
## Dependencies

- [Python Elasticsearch Client](https://elasticsearch-py.readthedocs.io/en/master/)
- [An Elasticsearch server](https://www.elastic.co/downloads/elasticsearch)
