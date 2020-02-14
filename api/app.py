# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import mysql.connector
import sys
import os
from flask import Flask, g, jsonify, request, make_response
from datetime import datetime

import api.database as db
from api.utils import validateApiKey, getUserlist
import api.validator as validation
from core.config import api_config

app = Flask(__name__)

app.config.update(**api_config)


@app.route('/userfeedback', methods=['GET'])
@validateApiKey
@getUserlist
def userfeedback(users):
    """API-endpoint for requesting userfeedback, 'user_id' must be one or more
    ids separated by comma."""
    return jsonify(db.getUserFeedback(users))


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


@app.route('/userinfo', methods=['GET'])
@validateApiKey
@getUserlist
def userinfo(users):
    """API-endpoint for requesting userdata, 'user_id' must be one or more ids
    separated by comma."""
    return make_response(jsonify({'userinfo': db.getUsers(users)}), 200)


@app.route('/articles', methods=['GET'])
@validateApiKey
def articles():
    """API-endpoint for requesting articleIDs, all articles added on the
    specified "date", if "date" is not specified it will the current date."""
    date = request.args.get('date', datetime.utcnow().strftime("%Y-%m-%d"))
    try:
        date = datetime.strptime(
            date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        return make_response(jsonify({'error': 'Invalid date format.'}, 400))
    articles = db.getArticleIDs(date)
    return make_response(jsonify({'articles': articles}), 200)


@app.route('/articledata', methods=['GET'])
@validateApiKey
def articledata():
    """API-endpoint for requesting articledata, 'article_id' must be one or more
    ids separated by comma."""
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

    articles = db.getArticleData(ids)
    return make_response(jsonify({'articles': articles}), 200)


@app.route('/recommendation', methods=['POST'])
@validateApiKey
@validation.validate_json(validation.recommendation)
def recommendation():
    """API-endpoint for inserting recommendations"""
    data = request.get_json().get('recommendations')
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    data = [(k, v['article_id'], g.sysID, v['explanation'], v['score'], now)
            for k, v in data.items() for v in v]

    db.insertRecommendations(data)
    return make_response(jsonify({'success': True}), 200)


@app.route('/recommendations', methods=['GET'])
@validateApiKey
@getUserlist
def recommendations(users):
    """API-endpoint for requesting user-recommendations,
     "user_id" must be one or more ids seperated by comma."""
    users = db.getUserRecommendations(users)
    return make_response(jsonify({'users': users}), 200)


@app.route('/', methods=['GET'])
def info():
    """Info response."""
    return make_response(jsonify({'info': "This is the ArXivDigest API"}), 200)


@app.teardown_appcontext
def teardownDb(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


if __name__ == '__main__':
    app.run(port=api_config.get('dev_port'), debug=True)
