# ArXivDigest: Personalized ArXiv Digest

Motivated by the accelerating pace at which scientific knowledge is being produced, we aim to provide a recommendation service that helps researchers to keep up with scientific literature. Based on their interest profiles, researchers can receive an email digest of the most recent papers published at arXiv at regular intervals. Further, users can give explicit feedback (likes/dislikes) to improve future recommendations.


## Evaluation Methodology

ArXivDigest provides an broker infrastructure that connects researchers that have signed up for the service (*users* for short) and experimental systems that provide content recommendations (*systems* for short). Systems generate personalized article recommendations for all users and make these available to the broker (by uploading them via an API). The broker takes all recommendations created for a given user, interleaves them, and sends out the top-k ranked articles in a digest email. Further, the broker registers implicit/explicit user feedback (and make these available to systems). This process is repeated daily.


## Evaluation Infrastructure

This evaluation framework consists of a front-end for *users* (researchers), a back-end, which includes a RESTful API for *experimental recommender systems*.

### Front-end:

  * Available (soon) at arxivdigest.org
  * After signing up, users can view the articles that are recommended to them. Articles can be "liked" to improve recommendations and for easily finding these articles later.
  * The front-end is implemented as Flask application ([source](frontend/)).

### Back-end:

  * [RESTful API](api/) for experimental recommender systems
    - For accessing article and user data.
    - For experimental recommender systems to upload personalized recommendations.
  * [Scraper](scraper/)
    - It continuously monitors the arXiv RSS feed for new articles, and downloads their metadata (authors, title, abstract, etc.)
  * [Batch processes](batch/)
    - It includes the interleaving mechanism for combining the recommendations of multiple experimental recommender systems. It also send the personalized recommendations to users in the form of daily digest emails.
  * [MySQL database](mysql/)
    - All data is stored in a MySQL database.


## Benchmark Organization

  * By using the service, users agree that their interest profiles, including the article recommendations they have been presented with and the implicit/explicit feedback they provided on each, would be made available to systems.
  * Systems are given a 2.5 hour window each day to download new content once it has been published on arXiv and generate recommendations for all registered ArXivDigest users.
  * System performance is monitored continuously over time. For system comparison, performance is measured during a designated evaluation period.

### HOWTO for Experimental Recommender Systems

Experimental recommender systems need to follow the following steps for submitting recommendations.

  1. Call [`GET /api/users`](/api/README.md#List%20of%20users) to get a list of user IDs.
  1. Call [`GET /api/userinfo?ids`](/api/README.md#User%20information) with user IDs as a parameter to get information about the users.
  1. Call [`GET /api/articles`](/api/README.md#List%20of%20articles) to get the list of article IDs that are may be returned as recommendation.
  1. Call [`GET /api/articledata?ids`](/api/README.md#Article%20data) with article IDs as a parameter to get information about the articles.
  1. Use the gathered information to generate personalized recommendations for users.
  1. Submit the generated recommendations to [`POST /api/recommendations`](/backend/README.md#Insert%20recommendations) in batches of maximum 100 users and 10 recommendations per user. Recommendations sent outside of the [recommendation period](#Arxiv%20schedule) will be ignored.

### Daily submission periods

According to [arXiv's release schedule](https://arxiv.org/help/submit#availability), new articles are released Monday to Friday 00:00 UTC.

The ArXivDigest Project accepts recommendations between 00:30 UTC and 03:00 UTC Monday til Friday.
