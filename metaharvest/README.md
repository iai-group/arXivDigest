# Bachelor
Personalized Scientific Literature Recommendation

### Metaharvest
Scraping is facilitated by the [OAI-api](https://arxiv.org/help/oa/index) provided by [arXiv](https://arxiv.org/) and the rss stream.  The [OAI-api](https://arxiv.org/help/oa/index) was chosen because it had the most well formatted metadata, and it also provided easy mechanisms for bulk harvesting.

##### Overview:
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
##### Database:

| Tables | Fields |
| ------------- | ------------- |
| articles  | articleID, title, description, doi, comments, license, journal, datestamp|
| articlecategories  | articleID, categoryID |
|articleAuthors| articleID, authorID, firstname, lastname|
|authorAffiliations| authorID, affiliations|
|categories| categoryID, category, subcategory|
   
##### Usage:
 The script can be run directly with the python command:
```console
python .\storeMetadata.py
```
Settings can be configured in config.json
##### Dependencies: 
- [Feedparser](https://github.com/kurtmckee/feedparser)
- [Python mysql connector](https://github.com/mysql/mysql-connector-python)

  
