# arXivDigest

Motivated by the accelerating pace at which scientific knowledge is being produced, we aim to provide a recommendation service that helps researchers to keep up with scientific literature. Based on their interest profiles, researchers can receive a personalized email digest of the most recent papers published at arXiv at regular intervals. Further, users can give explicit feedback (by saving articles) to improve future recommendations.


## Front-end (service)

After signing up, users can view the articles that are recommended to them. Articles can be saved to a personal library to improve recommendations and for easily finding these articles later.

The web front-end is implemented as Flask application (see [arxivdigest/frontend/](arxivdigest/frontend/)) and is available at https://arxivdigest.org.


## Back-end (living lab)

ArXivDigest operates as a "living lab". It provides a broker infrastructure that connects users of the service and experimental systems that provide content recommendations. See our [living lab page](Living_lab.md) for the details.

The core of this evaluation infrastructure is the arXivDigest API, which allows systems the access user data and to upload recommendations.  The API operates as a RESTful service at https://api.arxivdigest.org, with the code and documentation available under (arxivdigest/api)[arxivdigest/api].


## Contributors

ArXivDigest is developed and operated by the [IAI group](https://iai.group) at the University of Stavanger. Specifically, the development is led by [Krisztian Balog](http://krisztianbalog.com), and the implementation is being done by Øyvind Jekteberg and Kristian Gingstad as part of their former BSc and current MSc thesis projects.

We welcome contributions both on the high level (feedback and ideas) as well as on the more technical level (pull requests). Feel free to reach out to us at admin@arxivdigest.org.
