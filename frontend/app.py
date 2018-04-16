__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from flask import Flask, render_template, request, make_response, g, redirect, logging
from mysql import connector
import jwt
from views import general, admin, articles
from config import config, jwtKey


app = Flask(__name__)
app.register_blueprint(general.mod)
app.register_blueprint(articles.mod)
app.register_blueprint(admin.mod, url_prefix='/admin')
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
app.config['DEBUG'] = True  # remove this

from logging.config import dictConfig
import logging
logging.config.dictConfig(config.get("logging-config"))
logfile = logging.getLogger('file')


@app.after_request
def after_request_log(response):
    '''Logs the request to a file'''
    logfile.info("userID: %s - path: %s " % (g.user, request.full_path))
    return response


@app.before_request
def before_request():
    '''Checks authTokens before requests to check if users are logged in or not'''
    authToken = request.cookies.get("auth")
    if authToken is not None:
        try:
            payload = jwt.decode(authToken, jwtKey)
            g.user = payload['sub']
            g.email = payload['email']
            g.loggedIn = True
        except Exception as e:
            g.loggedIn = False
            print('JWT error:', e)
    else:
        g.loggedIn = False


@app.teardown_appcontext
def teardownDb(exception):
    '''Tears down the database connection after the request is done.'''
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run()
