# arXivDigest API

The arXivDigest API provides a set of endpoints for experimental recommender systems to get access to articles and user profiles, and to upload personalized recommendations for online evaluation.

Systems must have an active API key to access these endpoints.

## Endpoints

* [User data](#user-data)
  + [List of users](#list-of-users)
  + [User information](#user-information)
  + [User feedback articles](#user-feedback-articles)
  + [User feedback topics](#user-feedback-topics)
* [Article data](#article-data)
  + [List of articles](#list-of-articles)
  + [Article data](#article-data-1)
* [Recommendations](#recommendations)
  + [Insert article recommendations](#insert-article-recommendations)
  + [Article recommendation data](#article-recommendation-data)
  + [Insert topic recommendations](#insert-topic-recommendations)
  + [Topic recommendation data](#topic-recommendation-data)

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
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
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

`GET /user_info`

Returns the details of a given user (or list of users). Limited to 100 per request by default, this values can be [configured](#configurations).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:
  - `first_name`: first name
  - `last_name`: last name
  - `registered`: date of sign-up
  - `dblp_profile`: DBLP profile
  - `google_scholar_profile`: Google Scholar profile
  - `semantic_scholar_profile`: Semantic Scholar profile
  - `personal_website`: personal/organizational website
  - `topics`: list of topics user is interested in
  - `categories` : list of arXiv categories user is interested in
  - `organization`: the organization the user registered with

Other fields:
  - `error`: if something went wrong

Example:

  - Request: `GET /user_info?user_id=1,7`
  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "user_info": {
        "1": {
          "first_name": "John",
          "last_name": "Smith",
          "registered": "2020-01-17 17:06:23",
          "organization": "arXivDigest",
          "dblp_profile": "dblp.org/...",
          "google_scholar_profile": "scholar.google.com/...",
          "semantic_scholar_profile": "semanticscholar.org/author/..",
          "personal_website": "www.example.com",
          "categories": ["math","cs","cs.AI","astro-ph.CO"],
          "topics": [ "information retrieval",
                      "retrieval models",...
                    ]

            },...
          ]     
        }
        "7": {
          ...
        }
      }
    }
    ```

### User feedback articles

`GET /user_feedback/articles`

Returns the feedback on article recommendations recorded for a given user (or list of users).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields are returned in a JSON in the format, the article IDs are sorted descending by score:
```
    {
      "user_feedback": {
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
  - `feedback`: is the feedback stored in a dictionary of feedbak_type: datetime
    -  "seen_email":   datetime of when article was seen on email
    -  "seen_web":     datetime of when article was seen on web
    -  "clicked_email":datetime of when article was clicked in email
    -  "clicked_web":  datetime of when article was clicked on web
    -  "saved":        datetime of when article was saved


Other fields:
  - `error`: if something went wrong

Example feedback:

```
  "seen_email": null,
  "seen_web": 'Mon, 16 Mar 2020 00:00:00 GMT',
  "clicked_email": null,
  "clicked_web": 'Mon, 16 Mar 2020 00:00:00 GMT',
  "saved": null
````

Example request:

  - Request: `GET /user_feedback/articles?user_id=1,7`
  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "user_feedback": {
        "1": {
          "2020-03-17": [
          {"article-123":
            {
              "seen_email": null,
              "seen_web": '2020-03-17 17:13:53',
              "clicked_email": null,
              "clicked_web": '2020-03-17 17:13:53',
              "saved": null
            }
          },
          {"article-012": 1
            {
              "seen_email": null,
              "seen_web": '2020-03-17 17:13:53',
              "clicked_email": null,
              "clicked_web": '',
              "saved": null
            }
          },
          ...
           ]
        }
        "7": {
          ...
        }
      }
    }
    ```

### User feedback topics

`GET /user_feedback/topics`

Returns the feedback on topic recommendations recorded for a given user (or list of users).

Parameters:
  - `user_id` user ID, or a list of up to 100 user IDs, separated by a comma

Fields are returned in a JSON in the format, the topics are sorted descending by score:
```
    {
      "user_feedback": {
        user_id: {
           date: [
            {topic: feedback},
            {topic: feedback},
           ]
        }
      }
    }
```
Fields returned for each user:
  - `user_id`: ID of the user
  - `date`: Date the recommendation was originally given to the user
  - `topic`: topic that was recommended
  - `feedback`: is the feedback stored in a dictionary of {feedback_type: datetime}
    -  "seen":   datetime of when article was seen or null if not seen
    -  "clicked":     datetime of when topic was clicked or null if not clicked
    -  "state": USER_ADDED, USER_REJECTED, EXPIRED, REFRESHED, SYSTEM_RECOMMENDED_ACCEPTED, SYSTEM_RECOMMENDED_REJECTED

Explanations of different states:
  - USER_ADDED: The user added the topic themselves by writing it.
  - USER_REJECTED: The user removed a topic from their profile that was previously USER_ADDED.
  - EXPIRED: The topic was recommended, but the user did not interact with it within 24 hours of seeing this recommendation.
  - REFRESHED: The topic was recommended, but the user refreshed the topic suggestion list without interacting with it.
  - SYSTEM_RECOMMENDED_ACCEPTED: The topic was recommended and the user accepted it from the list.
  - SYSTEM_RECOMMENDED_REJECTED: The topic was recommended an the user rejected it from the list or manually removed it after first accepting it.

Other fields:
  - `error`: if something went wrong

Example request:

  - Request: `GET /user_feedback/topics?user_id=1,2,3`
  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```json
    {
      "user_feedback": {
        "1": {
          "2020-03-17": [
            {
              "higher education and career education": {
                "clicked": 2020-03-17 18:12:45,
                "seen": "2020-03-17 17:13:53",
                "state": "SYSTEM_RECOMMENDED_ACCEPTED"
              }
            },
            {
              "transportation planning": {
                "clicked": null,
                "seen": "2020-03-17 17:13:53"
                "state": "REFRESHED"
              }
            }
          ]
        },
        "2": {
          "2020-03-17": [
            {
              "transportation planning": {
                "clicked": null,
                "seen": "2020-03-17 17:13:53"
                "state": "EXPIRED"
              }
            }
          ]
        },
        "3": {}
      }
    }
    ```

## Article data

### List of articles

`GET /articles`

Returns a list of articles, which are candidates for recommendation, from the previous week.

Data returned:
  - `article_ids`: list of article ids:
  - `error`: if something went wrong

Example:

  - Request: `GET /articles`
  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "articles": [
          1111.2174, 1302.5663, 1407.6169, ...
        ]
    }
    ```

### Article data

`GET /article_data`

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

  - Request: `GET /article_data?article_id=123`
  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
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
          "date":"2020-03-17",
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

### Insert article recommendations

`POST /recommendations/articles`

Insert recommendations for articles to users, with a score describing how well it matches the users interests. Sending the same recommendation multiple times will update the score and explanations to the last received values. This allows reordering of already submitted recommendations, but assumes comparable scores across submissions. See the  [recommendation submission guide](/../../#howto-for-experimental-recommender-systems) for more information on how to submit recommendations.   

The maximal number of users that can be given recommendations in a single request, maximal number of recommendations per user and maximal length of explanations can be [configured](#configurations).

Header:
- `api-key` used to identify which system the recommendations come from

JSON:
  - `user_id` id of the user
  - `article_id` id of the article
  - `explanation` explanation for recommending this article
  - `score` score of the recommendation

Data returned:
  - `error`: if something went wrong
  - `article_ids`: list of article ids:

Example:
  - Request: `POST /recommendations/articles`

  - Header:
    ```
    {"Content-Type": "application/json",
     "api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
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
### Article recommendation data

`GET /recommendations/articles`

Returns article recommendation data for a given user (or list of users). By default it is limited to 100 users per request, but this can be [configured](#configurations).

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

  - Request: `GET /recommendations/articles?user_id=123`

  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
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

### Insert topic recommendations

`POST /recommendations/topics`

Insert recommendations for topics to users, with a score describing how well it matches the users interests. Will only accept topics that have not been recommended before or is added manually by a user. See the [recommendation submission guide](/../../#howto-for-experimental-recommender-systems) for more information on how to submit recommendations.   

The maximal number of users that can be given recommendations in a single request and the maximal number of recommendations per user can be [configured](#configurations).

Header:
- `api-key` used to identify which system the recommendations come from

JSON:
  - `user_id` id of the user
  - `topic` topic to recommend, containing only a..z, 0..9, space and dash
  - `score` score of the recommendation

Data returned:
  - `error`: if something went wrong

Example:
  - Request: `POST /recommendations/topics`

  - Header:
    ```
    {"Content-Type": "application/json",
     "api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - JSON:
    ```
    {
        "recommendations": {
        user_id: [
            {"topic": "Information Retrieval", "score": 2},
            {"topic": "Entity Oriented Search", "score": 3},
            {"topic": "Retrieval models", "score": 2}
        ],...
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
### Topic recommendation data

`GET /recommendations/topics`

Returns topic recommendation data for a given user (or list of users). By default it is limited to 100 users per request, but this can be [configured](#configurations).

Parameters:

- `user_id` User ID, or a list of up to 100 user IDs, separated by a comma

Fields returned for each user:

- `topic`: topic that was recommended
- `score`: score of the topic for this user
- `date`: date this recommendation was given
- `system_id`: id of the system which gave this recommendation

Other fields:
  - `error`: if something went wrong

Example:

  - Request: `GET /recommendations/topics?user_id=123`

  - Header:
    ```
    {"api-key": "355b36dc-7863-4c4a-a088-b3c5e297f04f"}
    ```
  - Response:
    ```
    {
      "users": {
        "123": {
          "Information Retrieval":[
              {"system_id":2,
              "score": 3,
              "date": "2020-01-17 17:06:23"},
              {"system_id":33,
              "score": 2,
              "date": "2020-01-17 17:06:23"}
          ],...
        }
      }
    }
    ```

## Configurations

These are the values that can be configured in the APIsection of config.json.

- `dev_port`: Port the server while be launched on while running in development mode.
- `max_content_length`: Maximum request size.
- `max_userinfo_request`: The maximal amount of users that info can be retrieved for in one request. More info on [endpoint](#user-information).
- `max_userid_request`: The maximal amount of userIds that can be retrieved in one request. More info on [endpoint](#list-of-users).
- `max_articledata_request`: The maximal amount of articles that info can be retrieved for in one request. More info on [endpoint](#article-data).
- `max_users_per_recommendation`:The maximal amount of users that recommendations can be submitted for in each request. More info on [endpoint](#insert-recommendations).
- `max_recommendations_per_user`: The maximal amount of articles that info can be recommended to each user in one request. More info on [endpoint](#insert-recommendations).
- `max_explanation_len`: The maximal length of an explanation for a recommendation. More info on [endpoint](#insert-recommendations).
