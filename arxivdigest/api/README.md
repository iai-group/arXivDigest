# ArXivDigest API

The arXivDigest API provides a set of endpoints for experimental recommender systems to get access to articles and user profiles, and to upload personalized recommendations for online evaluation.

Systems must have an active API key to access these endpoints.

## Configurations
These are the values that can be configured in the API-section of config.json.
- `dev_port`: Port the server while be launched on while running in development mode.
- `MAX_CONTENT_LENGTH`: Maximum request size.
- `MAX_USERINFO_REQUEST`: The maximal amount of users that info can be retrieved for in one request. More info on [endpoint](#user-information).
- `MAX_USERID_REQUEST`: The maximal amount of userIds that can be retrieved in one request. More info on [endpoint](#list-of-users).
- `MAX_ARTICLEDATA_REQUEST`: The maximal amount of articles that info can be retrieved for in one request. More info on [endpoint](#article-data).
- `MAX_RECOMMENDATION_USERS`:The maximal amount of users that recommendations can be submitted for in each request. More info on [endpoint](#insert-recommendations).
- `MAX_RECOMMENDATION_ARTICLES`: The maximal amount of articles that info can be recommended to each user in one request. More info on [endpoint](#insert-recommendations).
- `MAX_EXPLANATION_LEN`: The maximal length of an explanation for a recommendation. More info on [endpoint](#insert-recommendations).

## Endpoints
* [User data](#user-data)
  + [List of users](#list-of-users)
  + [User information](#user-information)
  + [User feedback](#user-feedback)
* [Article data](#article-data)
  + [List of articles](#list-of-articles)
  + [Article data](#article-data-1)
* [Recommendations](#recommendations)
  + [Insert recommendations](#insert-recommendations)
  + [Recommendation data](#recommendation-data)

## User data

### List of users

`GET /users`

Returns the list of user IDs, in batches of up to 10000, this limit can be [configured](#configurations)..

Parameters:
  - `from` start index of listing (default: 0)

Fields returned:
  - `num`: total number of users
  - `start`: start index of listing
  - `user_ids`: list of user IDs
  - `error`: if something went wrong


Example:

  - Request: `GET /users?from=1000`
  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "users": {
        "num": 1250,
        "start": 1000,
        "user_ids": [
          1001, 1002, 1004, 1005, 1006, ...
        ]
      }
    }
    ```

### User information

`GET /userinfo`

Returns the details of a given user (or list of users). Limited to 100 per request by default, this values can be [configured](#configurations).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:
  - `first_name`: first name
  - `last_name`: last name
  - `registered`: date of sign-up
  - `homepages`: list of homepages
  - `keywords`: list of self-supplied keywords
  - `categories` : list of arXiv categories user is interested in
  - `organization`: the organization the user registered with

Other fields:
  - `error`: if something went wrong

Example:

  - Request: `GET /userinfo?user_id=1,7`
  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "userinfo": {
        "1": {
          "first_name": "John",
          "last_name": "Smith",
          "registered": "2018-02-20",
          "homepages": [
            "http://dblp...",
            "http://scholar.google.com/..."
          ],
          "categories": ["math","cs","cs.AI","astro-ph.CO"]
          "keywords": [
            "information retrieval",
            "retrieval models"
          ]
        }
        "7": {
          ...
        }
      }
    }
    ```

### User feedback

`GET /userfeedback`

Returns the feedback data recorded for a given user (or list of users).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields are returned in a JSON in the format, the article IDs are sorted descending by score:
```
    {
      "userfeedback": {
        user_id: {
           date: [
            {article_id: feedback},
            {article_id: feedback},
           ]
        }
      }
    }
```
Fields returned for each user:
  - `user_id`: ID of the user
  - `date`: Date the recommendation was originally given to the user
  - `article_id`: ID of the article
  - `feedback`: is the feedback stored in binary in a five bit number
    -  "seen_email":   bit 0
    -  "seen_web":     bit 1
    -  "clicked_email":bit 2
    -  "clicked_web":  bit 2
    -  "liked":        bit 4


Other fields:
  - `error`: if something went wrong

Example feedback:

```
  "seen_email": 0,
  "seen_web": 1,
  "clicked_email": 0,
  "clicked_web": 1,
  "liked": 0
  feedback=b'01010'=10

  "seen_email": 1,
  "seen_web": 0,
  "clicked_email": 0,
  "clicked_web": 0,
  "liked": 0
  feedback=b'00001'=1
````

Example request:

  - Request: `GET /userfeedback?user_id=1,7`
  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "userfeedback": {
        "1": {
          "2018-05-10": [
          {"article-123": 12},
          {"article-012": 1},
          ...
           ]
        }
        "7": {
          ...
        }
      }
    }
    ```


## Article data

### List of articles

`GET /articles`

Returns a list of articles, which are candidates for recommendation, for a given day. If arXiv did not post anything at the requested date, the article_ids-field will be empty.

Parameters:
  - `date` date in YYYY-MM-DD format (default: current date)
Data returned:
  - `num`: total number of articles
  - `article_ids`: list of article ids:
  - `date` : date articles were added
  - `error`: if something went wrong

Example:

  - Request: `GET /articles?date=2018-02-20`
  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "articles": {
        "num": 1250,
        "article_ids": [
          1111.2174, 1302.5663, 1407.6169, ...
        ],
        "date"="2018-05-20"
      }
    }
    ```



### Article data

`GET /articledata`

Returns data for a given article (or list of articles). This is by default limited to 100 articles per request, but can be [configured](#configurations).

Parameters:

- `article_id` article ID, or a list of up to 100 article IDs, separated by a comma

Fields returned for each article:

  - `title`: title of article
  - `abstract`: description of article content
  - `license`: license
  - `date`: date article was added to arXivDigest
  - `doi`: the doi of the article (if available)
  - `comments`: arXiv comments on article (if available)
  - `journal-ref` : journal references (if available)
  - `authors`: list of authors
    - `firstname`: firstname of author (if available)
    - `keyname` :keyname of author (if available)
    - `affiliations`: for each author a list of their affiliations
  - `categories` : list of categories

Other fields:
  - `error`: if something went wrong

Example:

  - Request: `GET /articledata?article_id=123`
  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "articles": {
        "123": {
          "title": "XXX",
          "abstract": "XXX",
          "doi": "XXX",
          "comments": "XXX",
          "license": "XXX",
          "journal-ref": "XXX",
          "date":"2018-01-15",
          "authors":[
            {"firstname":"XXX",
             "keyname":"XXX",
             "affiliations":["XXX","XXX"]
            },
             {"firstname":"XXX",
             "keyname":"XXX",
             "affiliations":["XXX","XXX"]
            }
          ],
          "categories": ["cs.AI","astro-ph.CO"]
        }
      }
    }
    ```


## Recommendations

### Insert recommendations

`POST /recommendations`

Insert recommendations for articles to users, with a score describing how well it matches the users interests. Systems can submit recommendations in the periods specified in the [schedule](/../../#daily-submission-periods), recommendations submitted outside of the specified periods will be ignored. Systems can only recommend articles added to the arXiv the same day. See the  [recommendation submission guide](/../../#howto-for-experimental-recommender-systems) for more information on how to submit recommendations.   

The maximal number of users that can be given recommendations in a single request, maximal number of recommendations per user and maximal length of explanations can be [configured](#configurations).

Header:
- `api_key` used to identify which system the recomendations come from

JSON:
  - `user_id` id of the user
  - `article_id` id of the article
  - `explanation` explanation for recommending this article
  - `score` score of the recommendation

Data returned:
  - `error`: if something went wrong
  - `article_ids`: list of article ids:

Example:
  - Request: `POST /recommendations`

  - Header:
    ```
    {"Content-Type": "application/json",
     "api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - JSON:
    ```
    {
        "recommendations": {user_id: [
            {"article_id": "1107.2529", "score": 2, "explanation" : "reason"},
            {"article_id": "1308.1196", "score": 3, "explanation" : "reason"},
            {"article_id": "1312.5699", "score": 2, "explanation" : "reason"}
        ],
        user_id: [
            {"article_id": "1308.1196", "score": 10, "explanation" : "reason"},
            {"article_id": "1506.07383", "score": 6, "explanation" : "reason"}
        ]
      }
    }
      ```
  - Response:
    ```
    {
      "success": True
      "error" : "Some error"
    }
    ```
### Recommendation data

`GET /recommendations`

Returns recommendation data for a given user (or list of users). By default it is limited to 100 users per request, but this can be [configured](#configurations).

Parameters:

- `user_id` User ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:

- `article_id`: id of article
- `score`:score of article for this user
- `date`: date this recommendation was given
- `system_id`: id of the system which gave this recommendation

Other fields:
  - `error`: if something went wrong

Example:

  - Request: `GET /recommendations?user_id=123`

  - Header:
    ```
    {"api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "users": {
        "123": {
          "1151.1232":[
          {"system_id":"XXX",
          "score": "XXX",
          "date": "XXX"},
          {"system_id":"XXX",
          "score": "XXX",
          "date": "XXX"}
          ]
        }
      }
    }
    ```
