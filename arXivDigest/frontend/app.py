# -*- coding: utf-8 -*-

__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import jwt
from flask import Flask
from flask import g
from flask import request
from flask_assets import Environment

from arXivDigest.core.config import frontend_config
from arXivDigest.core.config import jwtKey
from arXivDigest.core.config import secret_key
from arXivDigest.frontend.views import admin
from arXivDigest.frontend.views import articles
from arXivDigest.frontend.views import general

app = Flask(__name__)
app.secret_key = secret_key
app.register_blueprint(general.mod)
app.register_blueprint(articles.mod)
app.register_blueprint(admin.mod, url_prefix='/admin')
app.config['MAX_CONTENT_LENGTH'] = frontend_config.get('MAX_CONTENT_LENGTH')
assets = Environment(app)

@app.before_request
def before_request():
    """Checks authTokens before requests to check if users are logged in or not"""
    authToken = request.cookies.get("auth")
    try:
        payload = jwt.decode(authToken, jwtKey)
        g.user = payload.get('sub', None)
        g.email = payload.get('email', None)
        g.admin = payload.get('admin', False)
        g.loggedIn = True
    except Exception:
        g.user = None
        g.email = None
        g.admin = False
        g.loggedIn = False


@app.teardown_appcontext
def teardownDb(exception):
    """Tears down the database connection after the request is done."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=frontend_config.get('dev_port'), debug=True)
