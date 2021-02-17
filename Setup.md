# Setup guide

This document contains instructions on how to install and deploy the arXivDigest service.  Information on the sample recommender system can be found in a [separate document](sample/).


## Initial setup

  0. Prerequisites:
      * [Python 3.6+](https://www.python.org/downloads/)
      * [MySQL server](https://www.mysql.com/)
  1. Clone this repository to a location of your choice (will be referred to as `REPO_PATH` below).
  2. Execute all SQL scripts under [db/](db/) in sequential order, starting with [db/database_v1.1.sql](db/database.sql) then v1.1, v2.0, etc.
  3. Run `pip install .` while inside `REPO_PATH` to install the `arxivdigest` Python package and its dependencies.
      * If installing with the purpose of development, use the command `pip install -e .` instead, to allow editing of the installed package.
      * If running the service under an Apache Web Server, you may need to grant access to the respective user (e.g., www-data on Ubuntu) to the installed package.
  4. Make sure to put [config.json](/config.json) in any of the below directories and update the settings specific to your system:
      * `~/arxivdigest/config.json`
      * `/etc/arxivdigest/config.json`
      * `%cwd%/config.json`
  5. Run the `init_topic_list.py` script in the `/scripts/` folder to populate the database with an initial topic list of general topics that the user can select from.
      * Under `REPO_PATH`, execute the command: `python scripts/init_topic_list.py`


## Installing updates

  1. Pull changes from this repository.
  2. Execute any new SQL scripts in [db/](db/).
  3. Run `pip install .` while inside `REPO_PATH` to update the package and its dependencies.
      * If needed, check permissions for the installed package.
  4. Update your local `config.json` file with any new configuration options introduced in [config.json](/config.json).

## Database

### Development

If you have Docker installed and do not want to set up MySQL locally, a [Dockerfile](db/Dockerfile) is provided for the database.
You can build and run this image with Docker Compose by running `docker-compose up`.

## Frontend and API

### Development mode

The frontend and API should be started by running `app.py` in their respective folder while developing.

Make sure that port 80 is free for the frontend and 5000 is free for the API (or change the frontend and API dev_ports in [config.json](/config.json)).


### Production mode

Instructions on how to deploy a Flask application can be found [here](http://flask.pocoo.org/docs/0.12/deploying/).

Below is an example WSGI file for the frontend (for the API, just replace "frontend" with "api" everywhere):

```py
#!/opt/anaconda3/bin/python
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/opt/anaconda3/lib/python3.6/site-packages/")

from arxivdigest.frontend.app import app as application
```

Remember to configure the settings in [config.json](config.json), especially the secret_keys. For more details, see [Frontend configuration](arxivdigest/frontend/README.md#configurations) and [API configuration](arxivdigest/api/README.md#configurations).

For best performance, static files should be served by the web server directly. To achieve this, `data_path` must be set in the config file. Then, the web server needs to be configured to reroute calls to `/static` to the folder named `static` that gets generated inside this location after the first launch. If not rerouted, these files will be served through Flask.


## Batch processes

There is a number of recurrent processes that should be automated to run at specific times.  This can be achieved by running these scripts with a cronjob.

The scripts should be run in the following order:

  * [Article scraper](scripts/scrape_arxiv.py): Should be run when arXiv releases new articles. The arXiv release schedule can be found [here](https://arxiv.org/help/submit#availability).  Note that articles are not released every day, so this script will not always insert any articles.
  * [Interleaver](scripts/interleave_articles.py): Should be run after the Article scraper.  Make sure that there is enough time for the recommender systems to generate recommendations between running the two scripts.
  * [Send digest mail](scripts/send_digest_mail.py): Should be run after the Interleaver, the amount of time in between can be varied based on when one wants to send out the digest mails.

