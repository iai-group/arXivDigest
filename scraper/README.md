# Scraper

Scraping is facilitated by the [OAI-api](https://arxiv.org/help/oa/index) provided by [arXiv](https://arxiv.org/) and the RSS stream.  The [OAI-api](https://arxiv.org/help/oa/index) was chosen because it contains well-formatted metadata, and it also provided easy mechanisms for bulk harvesting.


## Overview
The following methods can be used for harvesting metadata:

``getRecordsFromLastnDays(n):``

>Will return a dictionary of the metadata from all the articles from the previous n days, which can be used directly with insertIntoDB. harvestMetadataRss():

``harvestMetadataRss()``

>Will return a dictionary of the metadata from all the articles present in any of the rss-streams, which can be used directly with insertIntoDB.

``getRecord(id):``

>Retrives the metadata corresponding to the articleId provided.

``getCategories():``

>Returns a list of all the categories available at arXiv.

``insertIntoDB(metadata,conn):``

>This method takes in a dictionary of articles and a database connection, and then stores the articles in the supplied database.

## Database

This script will interact with the following tables in the database.

| Tables | Fields |
| ------------- | ------------- |
| articles  | article_ID, title, description, doi, comments, license, journal, datestamp|
| article_categories  | article_ID, category_ID |
|article_authors| article_ID, author_ID, firstname, lastname|
|author_affiliations| author_ID, affiliation|
|categories| category_ID, category, subcategory, category_name|

## Usage

Before running the script make sure to install the dependencies and configure the database connection in config.json.

 This script should be scheduled to run shortly after arXiv releases a new batch of articles, more about the arXiv schedule can be found [here](/../../#arxiv-schedule). This can be archived by running the script with a cronjob.

 The script can be run directly with the python command: 
```
python storeMetadata.py
```

If the script can't find a name for a category on arXiv or in its configured category names it will use the categoryID as its name. This should be manually resolved,by updating the configured categories and the name in the database, to give the best user experience.
## Dependencies

- [Feedparser](https://github.com/kurtmckee/feedparser)
- [Python mysql connector](https://github.com/mysql/mysql-connector-python)
