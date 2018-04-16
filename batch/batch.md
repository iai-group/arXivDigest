# Bachelor
Personalized Scientific Literature Recommendation

### Batch
This script will for each user combine the recommendations from the external systems into a single list of recommendations and inserts the new list into the database. It will also send email notification about the best matches to the user.

##### Overview:

##### Database:

| Tables | Fields |
| ------------- | ------------- |
| articles  | articleID, title, description, doi, comments, license, journal, datestamp|
|articleAuthors| articleID, authorID, firstname, lastname|
|users| user_ID, email, firstname, lastname, notification_interval, last_recommendation_date|
|system_recommendations| user_ID, article_ID, system_ID, score, recommendation_date|
|user_recommendations|user_ID, article_ID, system_ID, score, recommendation_date, seen_email, seen_web, clicked_email, clicked_web, liked, trace_like_email, trac_click_email|
   
##### Usage:
 The script can be run directly with the python command:
```console
python .\batch.py
```
Settings can be configured in config.json
##### Dependencies: 
- [Python mysql connector](https://github.com/mysql/mysql-connector-python)