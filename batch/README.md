# Batch processes

There is a daily batch process that combines the recommendations from the experimental recommender systems and inserts the combined ranking, for each user, into the database. It also sends out the digest emails to users.

## Overview

### Interleaving algorithm

The interleaving algorithm creates a single ranked list of recommendations for each user, and stores it in the database.

*TODO: more details*

### Digest email

When the interleaved recommendations have been created for each user, a digest email is sent to users. The digest email contains the top 3 articles for each user; additional recommendations may be viewed on the website.

## Database

This script interacts with the following tables in the database.

| Tables | Fields |
| ------------- | ------------- |
| articles  | article_ID, title, description, doi, comments, license, journal, datestamp|
|article_authors| article_ID, author_ID, firstname, lastname|
|users| user_ID, email, firstname, lastname, notification_interval, last_recommendation_date|
|system_recommendations| user_ID, article_ID, system_ID, score, recommendation_date|
|user_recommendations|user_ID, article_ID, system_ID, score, recommendation_date, seen_email, seen_web, clicked_email, clicked_web, liked, trace_like_email, trace_click_email|

## Usage

Before running the script make sure to install the dependencies and configure the database connection in `config.json`.

This script should be scheduled to run with a delay after MetaHarvest. This is to make sure that experimental recommender systems have time to submit recommendations between the two scripts. This can be archived by running the script with a cronjob.

The script can be run directly with the python command:
```
python batch.py
```

Settings can be configured in config.json

## Dependencies

- [Python mysql connector](https://github.com/mysql/mysql-connector-python)
