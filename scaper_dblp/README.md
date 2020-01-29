# Scraper for DBLP dump file

Scraping is facilitated by the [DBLP dump](https://dblp.uni-trier.de/xml/dblp.xml.gz) that can be downloaded as a zipped file.

## Overview
Following functions are used in the execution of the scraper_dblp.py script:

``download_dump(dump_url, savepath):``

>Will download the dblp dump file and save it to the provided save path

``find_dblp_titles(savepath):``

>Loads the file and scans it looking for titles. Returns a list of all paper titles in the dump.

``find_dblp_keywords(title_list, max_keyword_lenght):``

>Uses Rake on the provided list of titles to create a dictionary of keywords and scores.

``match_keywords(database_conn, title_list, keyword_dict, max_keyword_lenght):``

>Will match the scraped titles with what keywords they contain. Then saves the title, keyword, score triplet to the database.

## Database

This script interacts with one database table shown below.

| Tables | Fields |
| keywords | id, title, keyword, score |

## Usage

Before running the script make sure to install the dependencies and configure the database connection in config.json.

The dump is updated daily, but with no version number and unknown number of changes. Therefore this script can be scheduled to run as often as one wants to update the list of articles and keywords, but could be once every week.

 The script can be run directly with the python command: 
```
python scraper_dblp.py
```

## Depencencies

- [Python mysql connector](https://github.com/mysql/mysql-connector-python)
- [nltk](https://www.nltk.org/)