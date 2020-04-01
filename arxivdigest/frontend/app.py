# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import os
import pathlib
import shutil

import jwt
from flask import Flask
from flask import g
from flask import request
from flask_assets import Bundle
from flask_assets import Environment
from flask_wtf import CSRFProtect

from arxivdigest.core.config import config_frontend
from arxivdigest.core.config import jwtKey
from arxivdigest.core.config import secret_key
from arxivdigest.frontend.views import admin
from arxivdigest.frontend.views import articles
from arxivdigest.frontend.views import general
from arxivdigest.frontend.views import topics
from arxivdigest.frontend.views.articles import topic_flag

app = Flask(__name__)
app.secret_key = secret_key
app.register_blueprint(general.mod)
app.register_blueprint(articles.mod)
app.register_blueprint(admin.mod, url_prefix='/admin')
app.config['max_content_length'] = config_frontend.get('max_content_length')

if topic_flag:
    app.register_blueprint(topics.mod)

csrf = CSRFProtect(app)
assets = Environment(app)
if config_frontend.get('data_path', None):
    data_path = config_frontend['data_path']
    cache_path = os.path.join(data_path, 'cache', '.webassets-cache')
    static_path = os.path.abspath(os.path.join(data_path, 'static'))

    pathlib.Path(cache_path).mkdir(parents=True, exist_ok=True)

    assets.cache = os.path.abspath(cache_path)
    assets.directory = os.path.abspath(static_path)
    app.static_folder = static_path

    if os.path.exists(static_path):
        shutil.rmtree(static_path)
    shutil.copytree(os.path.join(app.root_path, 'static'), static_path)

# Do not automatically build assets in deployment for performance
assets.auto_build = False
assets.append_path(os.path.join(app.root_path, 'uncompiled_assets'))

js_bundle = Bundle('javascript/autocomplete.js',
                   'javascript/forms.js',
                   'javascript/articlelist.js',
                   'javascript/admin.js',
                   filters='jsmin',
                   output='generated/js/base.%(version)s.js')

if topic_flag:
    js_bundle = Bundle('javascript/autocomplete.js',
                   'javascript/forms.js',
                   'javascript/articlelist.js',
                   'javascript/admin.js',
                   'javascript/topics.js',
                   filters='jsmin',
                   output='generated/js/base.%(version)s.js')

css_bundle = Bundle('css/style.css',
                    filters='cssmin',
                    output='generated/css/base.%(version)s.css')

assets.register('js_base', js_bundle)
assets.register('css_base', css_bundle)
js_bundle.build()
css_bundle.build()


@app.before_request
def before_request():
    """Checks authTokens before requests to check if users are logged in or not"""
    authToken = request.cookies.get("auth")
    try:
        payload = jwt.decode(authToken, jwtKey)
        g.user = payload.get('sub', None)
        g.email = payload.get('email', None)
        g.admin = payload.get('admin', False)
        g.inactive = payload.get('inactive', True)
        g.loggedIn = True
    except Exception:
        g.user = None
        g.email = None
        g.admin = False
        g.loggedIn = False
        g.inactive = True


@app.teardown_appcontext
def teardownDb(exception):
    """Tears down the database connection after the request is done."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    assets.auto_build = True
    app.config['ASSETS_DEBUG'] = True
    app.run(port=config_frontend.get('dev_port'), debug=True)
