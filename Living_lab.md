# Living lab

ArXivDigest operates as a living lab platform. It means that third-party researchers can experiment with novel recommendation approaches ("recommendations AI"), and the generated suggestions will be shown to users of the arXivDigest service.  This allows for realistic, in situ evaluation with real users.  Further, user interactions can be utilized for improving recommendation and explanation capabilities.

## Methodology

ArXivDigest provides a broker infrastructure that connects *users* (people who signed up for the arXivDigest service) and *systems* (methods developed for providing content recommendations).  

  * By using the service, users agree that their interest profiles, including the article recommendations they have been presented with and the implicit/explicit feedback they provided on each, would be made available to systems.
  * Systems are given a 2.5 hour window each day to download new content once it has been published on arXiv, generate recommendations for any or all registered arXivDigest users, and upload these via the [arXivDigest API](/arxivdigest/api).
  * The broker takes all recommendations created for a given user, interleaves them, and shows the top-k recommendations to the user.  See the section on [interleaving](#interleaving) for the specifics.
  * System performance is monitored continuously over time. For system comparison, performance is measured during a designated evaluation period.


## Components

The evaluation framework consists of the following components:

  * [arXivDigest API](/arxivdigest/api/)
    - A RESTful service for experimental recommender systems to access article and user data and to upload personalized recommendations.
  * Batch processes scheduled to run daily:
    - [Scraper](scripts/scrape_arxiv.py): Checks the arXiv RSS feed and downloads new articles.
    - [Interleaving](scripts/interleave_articles.py): combines article recommendations of multiple experimental recommender systems by interleaving them into a single list.
    - [Digest email](scripts/send_digest_mail.py): Sends personalized article recommendations to users in the form of daily/weekly digest emails.
  * Evaluation
    - Compares how users interacted with different systems over a period of time and generates statistics.

If you want to (i) operate a service yourself or (ii) set up a local copy for development purposes,
check the [Setup guide](/Setup.md) for information on how to run the system.


## Guide for participants

Experimental recommender systems need to follow the following steps for submitting recommendations.  The API is available at https://api.arxivdigest.org.

  1. Call [`GET /users`](/arxivdigest/api#list-of-users) to get a list of user IDs.
  1. Call [`GET /user_info?ids`](/arxivdigest/api#user-information) with user IDs as a parameter to get information about the users.
  1. Call [`GET /articles`](/arxivdigest/api#list-of-articles) to get the list of article IDs that are may be returned as recommendation.
  1. Call [`GET /article_data`](/arxivdigest/api#article-data) with article IDs as a parameter to get information about the articles.
  1. Use the gathered information to generate personalized recommendations for users.
  1. Submit the generated recommendations to [`POST /recommendations/articles`](/arxivdigest/api#insert-article-recommendations) in batches of maximum 100 users and 10 recommendations per user. Recommendations sent outside of the [recommendation period](#daily-submission-periods) will not be considered by the daily interleaving process.


#### Daily submission periods

According to [arXiv's release schedule](https://arxiv.org/help/submit#availability), new articles are released Monday to Friday 00:00 UTC.

ArXivDigest accepts recommendations between 00:30 UTC and 03:00 UTC Monday til Friday.


## Interleaving

Currently, there are two main types of content that can be recommended: articles and topics. The interleaving process works slightly differently for the two.

### Article recommendations

At each given (week)day, the interleaving process considers, from each system, the highest scoring articles from the past 7 days that were submitted for a given user.  That is, systems can think of the article recommendation process as pushing items to a priority queue, where items older than 7 days are removed from the queue.
The top recommendations from the various systems are interleaved for users daily.

Digest emails are sent out daily or weekly (depending on users' preference).  The weekly digest email if essentially a concatenation of the content of the daily emails, i.e., it contains the respective interleaved lists for each day.

User may leave feedback on specific recommendations, which is made available to systems.

### Topic recommendations

*COMING SOON*
