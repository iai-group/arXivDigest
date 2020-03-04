# ArXivDigest front-end

The front-end (running at http://arxivdigest.org) is implemented as a Flask application.  It provides users with a website for viewing and interacting with the recommendations created for them. The recommendated science papers can be sorted on time intervals such as today, this week, this month and all time. They can also be sorted by title or score. It also includes an admin panel for managing experimental recommender systems.

## Overview

Routes available:

``/ @requiresLogin``

>Returns index page and dirctionary of index page settings, drop down values and articles as sub dictionary.

``/signup [GET]``

>Returns signup page if you're not logged in. Else returns index page.

``/signup [POST]``

>Goes to signup function. Returns a jwt token and index page if successful. Else returns error message and signup page.

``/logout [GET]``

>Goes to logout function. Logs out user and sets token expires=0. Returns index page.

``/profile [GET] @requiresLogin``

>Returns user profile page with user information.

``/modify [GET] @requiresLogin``

>Returns modify user page.

``/modify [POST] @requiresLogin``

>Returns user profile page if successful. Else return error and modify page.

``/passwordChange [GET] @requiresLogin``

>Returns page for change of password.

``/passwordChange [POST] @requiresLogin``

>Returns profile page if successful. Else returns error and password change page.

``/login [GET]``

>Returns login page if you're not logged in. Else returns index page.

``/login [POST]``

>Returns token in successful login. Else returns error and loginpage.

``/likedarticles [GET] @requiresLogin``

>Returns liked articles page with dictionary of liked articles.

``/like/<articleID>/<state> [GET] @requiresLogin``

>Likes or unlikes articles from web, depending on current state. Returns "Success" or "Fail".

``/author_keywords/<author_url> [GET]``

>Scrapes the url provided for paper titles and looks up titles in database to find matching keywords. Returns "" or list of keywords.

``/keyword_feedback/<keyword>/<opinion> [GET]``

>Stores the suggested keyword for an user along with the users opinion on that keywors (discarded or approved).

``/mail/like/<int:userID>/<string:articleID>/<uuid:trace> [GET]``

>Likes article directly from email based on userid, articleid and a trace from the email.

``/mail/read/<int:userID>/<string:articleID>/<uuid:trace> [GET]``

>Records if article was clicked from email.

``/click/<string:articleId> [GET] @requiresLogin``

>Records if article was clicked from web. Returns redirect to arxiv info page or article pdf depending on where user clicked.

``/admin [GET] @requiresLogin``

>Return admin page and dictionary of systems in database.

``/systems/get [GET] @requiresLogin``

>Returns list of systems from db.

``/admins/get [GET] @requiresLogin``

>Returns list of admins from db.

``/systems/toggleActive/<int:systemID>/<state> [GET] @requiresLogin``

>Activate/deactivate system with systemID depending on state.

``/general [GET] @requiresLogin``

>Returns number of users and articles.

``/system/register [POST]``

>Sends new systems data from web form to database function. Returns register system page or error.

``/system/register [GET]``

>Returns page for system registration.

``@requiresLogin``

>Decorator that checks if you are logged in before accessing the route it is used on. If you are not logged in it returns login page and error message.

## Database

| Tables | Fields |
| ------------- | ------------- |
| users | user_ID, email, salted_hash, firstname, lastname, keywords, notification_interval, registered, admin, last_recommendation_date, company|
| user_categories | user_ID, category_ID |
| user_webpages | user_ID, url |
| articles | article_ID, title, abstract, doi, comments, licence, journal, datestamp |
| article_authors | author_ID, article_ID, firstname, lastname |
| article_categories | article_ID, category_ID |
| author_affiliations | author_ID, affiliation |
| categories | category_ID, category, subcategory, category_name |
| system_recommendations | user_ID, article_ID, system_ID, score, recommendation_date |
| systems | system_ID, api_key, system_name, active |
| user_recommendations | user_ID, article_ID, system_ID, score, recommendation_date, seen_email, seen_web, clicked_email, clicked_web, liked, trace_like_email, trace_click_email |
| keywords | title, keyword, score |
| keyword feedback | user_id, keyword, feedback, datestamp |

## Setup

Read the [Setup guide](../../Setup.md).

## Dependencies

- [Mysql connector for python](https://dev.mysql.com/doc/connector-python/en/)
- [Json Web Tokens](https://github.com/jpadilla/pyjwt) 
- [Flask](http://flask.pocoo.org/)
- [Passlib](https://passlib.readthedocs.io/en/stable/index.html)
