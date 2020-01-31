# Sample System

This folder contains a sample implementation of a recommender system.

## Overview

The system has several stages of execution:
- First makes sure an Elasticsearch index with the correct mappings exist. If not it will be created.
- Then it queries the arXivDigest API for articles to add to the index. These are the articles that will be candidate recommendations later.
- Next the system queries the arXivDigest API for user information. This is the information which the system bases its personalized recommendations on.
- The system then creates personalized recommendations for each user, currently the recommendations are created by searching the Elasticsearch index with the users keywords for the best matching articles. 
- Finally the articles found for each user are submitted to the arXivDigest API as recommendations. 

## Usage

Before running the system make sure that an Elasticsearch server is running and to configure the needed settings. 
API url, Elasticsearch url and index name can be configured at the top of system.py.

The system can by run by the command: ``python system.py``
    
## Dependencies

- [Python Elasticsearch Client](https://elasticsearch-py.readthedocs.io/en/master/)
- [An Elasticsearch server](https://www.elastic.co/downloads/elasticsearch)
