# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from datetime import datetime

from flask import Flask
from flask import g
from flask import jsonify
from flask import make_response
from flask import request

import arxivdigest.api.database as db
import arxivdigest.api.validator as validation
from arxivdigest.api.utils import getUserlist
from arxivdigest.api.utils import validateApiKey
from arxivdigest.core.config import api_config

app = Flask(__name__)

app.config.update(**api_config)


@app.route('/user_feedback/articles', methods=['GET'])
@validateApiKey
@getUserlist
def user_feedback_articles(users):
    """API-endpoint for requesting user_feedback for articles, 'user_id' must be
    one or more ids separated by comma."""
    return jsonify(db.get_user_feedback_articles(users))


@app.route('/users', methods=['GET'])
@validateApiKey
def users():
    """API-endpoint for fetching userIDs, ids will be returned in batches
    starting from 'fromID'.
    If 'fromID' is unspecified 0 will be used as default."""
    try:
        fromID = int(request.args.get('from', 0))
        if fromID < 0:
            return make_response(jsonify({'error': '"from" must be positive'}), 400)
    except Exception:
        err = '"from" must be an integer'
        return make_response(jsonify({'error': err}), 400)

    users = db.getUserIDs(fromID, app.config['MAX_USERID_REQUEST'])
    return make_response(jsonify({'users': users}), 200)


@app.route('/user_info', methods=['GET'])
@validateApiKey
@getUserlist
def user_info(users):
    """API-endpoint for requesting userdata, 'user_id' must be one or more ids
    separated by comma."""
    return make_response(jsonify({'user_info': db.getUsers(users)}), 200)


@app.route('/articles', methods=['GET'])
@validateApiKey
def articles():
    """API-endpoint for requesting articleIDs of articles from the last 7
    days."""
    return make_response(jsonify({
        'articles': db.get_article_ids_past_seven_days()}), 200)


@app.route('/article_data', methods=['GET'])
@validateApiKey
def article_data():
    """API-endpoint for requesting article_data, 'article_id' must be one or
    more ids separated by comma."""
    try:
        ids = request.args.get('article_id').split(',')
    except Exception:
        return make_response(jsonify({'error': 'No IDs supplied.'}, 400))
    if (len(ids) > app.config['MAX_ARTICLEDATA_REQUEST']):
        err = 'You cannot request more than %s articles at a time.' % app.config[
            'MAX_ARTICLEDATA_REQUEST']
        return make_response(jsonify({'error': err}), 400)

    articles = db.checkArticlesExists(ids)
    if len(articles) > 0:
        err = 'Could not find articles with ids: %s.' % ', '.join(articles)
        return make_response(jsonify({'error': err}), 400)

    articles = db.get_article_data(ids)
    return make_response(jsonify({'articles': articles}), 200)


@app.route('/recommendations/articles', methods=['POST'])
@validateApiKey
@validation.validate_json(validation.recommendation)
def article_recommendations():
    """API-endpoint for inserting article recommendations"""
    data = request.get_json().get('recommendations')
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    data = [(k, v['article_id'], g.sysID, v['explanation'], v['score'], now)
            for k, v in data.items() for v in v]

    db.insert_article_recommendations(data)
    return make_response(jsonify({'success': True}), 200)


@app.route('/recommendations/articles', methods=['GET'])
@validateApiKey
@getUserlist
def article_recommendations(users):
    """API-endpoint for requesting user-recommendations of articles,
     "user_id" must be one or more ids seperated by comma."""
    users = db.get_article_recommendations(users)
    return make_response(jsonify({'users': users}), 200)


@app.route('/', methods=['GET'])
def info():
    """Info response."""
    return make_response(jsonify({'info': "This is the arXivDigest API"}), 200)


@app.teardown_appcontext
def teardownDb(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=api_config.get('dev_port'), debug=True)
