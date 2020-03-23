# ArXivDigest: Personalized arXiv Digest

Motivated by the accelerating pace at which scientific knowledge is being produced, we aim to provide a recommendation service that helps researchers to keep up with scientific literature. Based on their interest profiles, researchers can receive an email digest of the most recent papers published at arXiv at regular intervals. Further, users can give explicit feedback (by saving articles) to improve future recommendations.


## Evaluation Methodology

ArXivDigest provides an broker infrastructure that connects researchers that have signed up for the service (*users* for short) and experimental systems that provide content recommendations (*systems* for short). Systems generate personalized article recommendations for all users and make these available to the broker (by uploading them via an API). The broker takes all recommendations created for a given user, interleaves them, and sends out the top-k ranked articles in a digest email. Further, the broker registers user feedback (and make these available to systems). This process is repeated daily.


## Evaluation Infrastructure

This evaluation framework consists of a front-end for *users* (researchers), a back-end, which includes a RESTful API for *experimental recommender systems*.

Check the [Setup guide](/Setup.md) for information on how to run the system.

### Front-end:

  * Is available at https://arxivdigest.org.
  * After signing up, users can view the articles that are recommended to them. Articles can be saved to a personal library to improve recommendations and for easily finding these articles later.
  * The front-end is implemented as Flask application ([source](arxivdigest/frontend/)).

### Back-end:

  * [RESTful API](arxivdigest/api/) for experimental recommender systems
    - For accessing article and user data.
    - For experimental recommender systems to upload personalized recommendations.
  * [Scraper](scraper/)
    - It continuously monitors the arXiv RSS feed for new articles, and downloads their metadata (authors, title, abstract, etc.)
  * [Interleave processes](scripts/interleave_articles.py)
    - It includes the interleaving mechanism for combining the article recommendations of multiple experimental recommender systems. 
  * [Digest email processes](scripts/send_digest_mail.py)
    - It sends the personalized recommendations to users in the form of daily digest emails. 
  * [Init topics script](scripts/init_topic_list.py)
    - It adds a initial list of topics to the database.
  * [Database](db/)
    - All data is stored in a MySQL database.
  * Evaluation
    - Compares how users interacted with different systems over a period of time and prints the results

## Evaluation Methodology

  * By using the service, users agree that their interest profiles, including the article recommendations they have been presented with and the implicit/explicit feedback they provided on each, would be made available to systems.
  * Systems are given a 2.5 hour window each day to download new content once it has been published on arXiv and generate recommendations for all registered arXivDigest users.
  * System performance is monitored continuously over time. For system comparison, performance is measured during a designated evaluation period.

### HOW-TO for Experimental Recommender Systems

Experimental recommender systems need to follow the following steps for submitting recommendations.  The API is available at https://api.arxivdigest.org.

  1. Call [`GET /users`](/arxivdigest/api#list-of-users) to get a list of user IDs.
  1. Call [`GET /user_info?ids`](/arxivdigest/api#user-information) with user IDs as a parameter to get information about the users.
  1. Call [`GET /articles`](/arxivdigest/api#list-of-articles) to get the list of article IDs that are may be returned as recommendation.
  1. Call [`GET /article_data`](/arxivdigest/api#article-data) with article IDs as a parameter to get information about the articles.
  1. Use the gathered information to generate personalized recommendations for users.
  1. Submit the generated recommendations to [`POST /recommendations/articles`](/arxivdigest/api#insert-article-recommendations) in batches of maximum 100 users and 10 recommendations per user. Recommendations sent outside of the [recommendation period](#daily-submission-periods) will be ignored.

### Daily submission periods

According to [arXiv's release schedule](https://arxiv.org/help/submit#availability), new articles are released Monday to Friday 00:00 UTC.

The arXivDigest project accepts recommendations between 00:30 UTC and 03:00 UTC Monday til Friday.


### Contributors

- Concept and architecture design: [Krisztian Balog](http://krisztianbalog.com)
- The current implementation was done by Øyvind Jekteberg and Kristian Gingstad as part of their BSc thesis project
