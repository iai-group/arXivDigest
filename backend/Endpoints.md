# API endpoints

## User data

### List of users

`GET /api/users`

Returns the list of user IDs, in batches of 10000, that are registered.

Parameters:
  - `from` start index of listing (default: 0)

Fields returned:
  - `num`: total number of users
  - `start`: start index of listing
  - `user_ids`: list of user IDs
  - `error`: if somthing went wrong


Example:

  - Request: `GET /api/users?from=1000`
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

`GET /api/userinfo`

Returns the details of a given user (or list of users).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:
  - `first_name`: first name
  - `last_name`: last name
  - `registered`: date of sign-up
  - `homepages`: list of homepages
  - `keywords`: list of self-supplied keywords
  - `categories` : list of arXiv categories user is interested in
  - `error`: if somthing went wrong

Example:

  - Request: `GET /api/userinfo?user_id=1,7`
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

`GET /api/userfeedback`

Returns the feedback data recorded for a given user (or list of users).

*TODO*


## Article data

### List of articles

`GET /api/articles`

Returns a list of articles, which are candidates for recommendation, for a given day.

Parameters:
  - `date` date in YYYY-MM-DD format (default: most recent date with articles) 
Data returned:
  - `num`: total number of articles
  - `article_ids`: list of article ids:
  - `date` : date articles were added
  - `error`: if somthing went wrong

Example:

  - Request: `GET /api/articles?date=2018-02-20`
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

`GET /api/articledata`

Returns data for a given article (or list of articles).

Parameters:

- `article_id` article ID, or a list of up to 100 article IDs, separated by a comma

Fields returned for each article:

  - `title`: title of article
  - `abstract`: description of article content
  - `license`: license
  - `doi`: the doi of the article (if available)
  - `comments`: arxiv comments on article (if available)
  - `journal-ref` : journal references (if available)
  - `authors`: list of authors
    - `firstname`: firstname of author (if available)
    - `keyname` :keyname of author (if available)
    - `affiliations`: for each author a list of their affiliations
  - `categories` : list of categories
  - `error`: if somthing went wrong

Example:

  - Request: `GET /api/articledata?article_id=123`
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

`POST /api/recommendations`

Insert recommendations for articles to users, with a score describing how well it matches the users interests

Header:
- `api_key` used to identify wich system the recomendations come from

JSON:
  - `article_id` id of the article
  - `score` score of the recommendation

Data returned:
  - `error`: if somthing went wrong
  - `article_ids`: list of article ids:

Example:
  - Request: `POST /api/recommendations`

  - Header:
    ```
    {"Content-Type": "application/json",
     "api_key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - JSON:
    ```
    {
        "recommendations": {1: [
            {"article_id": "1107.2529", "score": 2},
            {"article_id": "1308.1196", "score": 3},
            {"article_id": "1312.5699", "score": 2}
        ], 
        2: [
            {"article_id": "1308.1196", "score": 10},
            {"article_id": "1506.07383", "score": 6}
        ]
      }
    }
      ```
  - Response:
    ```
    {
      "success": "Success"
      "error" : "Some error"
    }
    ```
### Recommendation data

`GET /api/recommendations`

Returns recommendation data for a given user (or list of users).

Parameters:

- `user_id` User ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:

  - `article_id`: id of article
  - `score`:score of article for this user
  - `date`: date this recommendation was given
  - `system_id`: id of the system wich gave this recommendation
  - `error`: if somthing went wrong

Example:

  - Request: `GET /api/recommendations?user_id=123`

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
