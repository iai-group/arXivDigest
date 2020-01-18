# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from functools import wraps
from flask import Flask, g, jsonify, request, make_response
from flask import current_app as app
import api.database as db
from datetime import datetime


def validate_json(validator_func):
    '''Decorator for validating submitted json using supplied validator function.
       Validator functions should take a json as input argument, and return none if valid,
       or a response if something is invalid.'''
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json = request.get_json()
            if not json:
                return make_response(jsonify({'success': False, 'error': 'No JSON submitted.'}), 400)
            error = validator_func(json)
            if error:
                return error
            return f(*args, **kwargs)
        return wrapper
    return decorator


def recommendation(json):
    json = json.get('recommendations')
    if not json:
        return make_response(jsonify({'success': False, 'error': 'No recommendations submitted.'}), 400)

    if len(json) > app.config['MAX_RECOMMENDATION_USERS']:
        err = 'Requests must not contain more than %s users.' % app.config[
            'MAX_RECOMMENDATION_USERS']
        return make_response(jsonify({'success': False, 'error': err}), 400)

    for user in json:
        if len(user) > app.config['MAX_RECOMMENDATION_ARTICLES']:
            err = 'Requests must not contain more than %s articles per user.' % app.config[
                'MAX_RECOMMENDATION_ARTICLES']
            return make_response(jsonify({'success': False, 'error': err}), 400)

    not_found_users = db.checkUsersExists([user_id for user_id in json])
    if len(not_found_users) > 0:
        err = 'No users with ids: %s.' % ', '.join(not_found_users)
        return make_response(jsonify({'success': False, 'error': err}), 400)

    articleIDs = [article['article_id']
                  for user in json.values() for article in user]
    articles = db.checkArticlesExists(articleIDs)
    if len(articles) > 0:
        err = 'Could not find articles with ids: %s.' % ', '.join(articles)
        return make_response(jsonify({'success': False, 'error': err}), 400)

    today = datetime.utcnow().strftime("%Y/%m/%d")
    articlesToday = db.getArticleIDs(today)['article_ids']
    notToday = (set(articlesToday) & set(articleIDs) ^ set(articleIDs))
    if notToday:
        err = 'These articles are not from todays batch: %s.' % ', '.join(
            notToday)
        return make_response(jsonify({'success': False, 'error': err}), 400)

    for recommendations in json.values():
        for recommendation in recommendations:
            try:
                float(recommendation['score'])
            except Exception:
                return make_response(jsonify({'success': False,
                                              'error': 'Score must be a float'}), 400)

            if not "explanation" in recommendation:
                return make_response(jsonify({'success': False,
                                              'error': 'Recommendations must include explanation.'}), 400)

            if len(recommendation["explanation"]) > app.config['MAX_EXPLANATION_LEN']:
                err = 'Explanations must be shorther than %s.' % app.config['MAX_EXPLANATION_LEN']
                return make_response(jsonify({'success': False, 'error': err}), 400)
