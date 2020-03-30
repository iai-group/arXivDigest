# Scraper

Scraping is facilitated by the [OAI-api](https://arxiv.org/help/oa/index) provided by [arXiv](https://arxiv.org/) and the RSS stream.  The [OAI-api](https://arxiv.org/help/oa/index) was chosen because it contains well-formatted metadata, and it also provided easy mechanisms for bulk harvesting.

If the scraper is unable find a name for a category on arXiv or in its configured category names it will use the categoryID as its name. This should be manually resolved,by updating the configured categories and the name in the database, to give the best user experience.


