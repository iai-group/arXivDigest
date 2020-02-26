# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, The ArXivDigest Project'

from datetime import datetime
from functools import wraps

from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask import request

import api.database as db


def validate_json(validator_func):
    """Decorator for validating submitted json using supplied validator function.
       Validator functions should take a json as input argument, and return none
       if valid, or a (msg,status) tuple if something is invalid."""

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            json = request.get_json()
            if not json:
                return make_response(
                    jsonify({'success': False, 'error': 'No JSON submitted.'}),
                    400)
            error = validator_func(json)
            if error:
                return make_response(
                    jsonify({'success': False, 'error': error[0]}), error[1])
            return f(*args, **kwargs)

        return wrapper

    return decorator


def recommendation(json):
    """Validator function for json submitted to the recommendation insertion
    endpoint."""
    json = json.get('recommendations')
    if not json:
        return 'No recommendations submitted.', 400

    if len(json) > app.config['MAX_RECOMMENDATION_USERS']:
        return 'Requests must not contain more than %s users.' % app.config[
            'MAX_RECOMMENDATION_USERS'], 400

    check_funcs = {nonexistent_users,
                   # functions that validate different properties of the json
                   too_many_recommendations,
                   contains_ineligible_articles,
                   score_is_not_float,
                   missing_explanation,
                   too_long_explanation, }

    for check_func in check_funcs:
        err = check_func(json)
        if err:
            return err
    return None


def nonexistent_users(json):
    """Returns false if all users exist.
    Returns errormessage and status code if not."""
    user_ids = [user_id for user_id in json]
    if len(user_ids) is 0:
        return 'Request must contain at least one user.', 400
    not_found_users = db.checkUsersExists(user_ids)
    if len(not_found_users) > 0:
        return 'No users with ids: %s.' % ', '.join(not_found_users), 400
    return False


def too_many_recommendations(json):
    """Returns false if no user got more recommendations then the limit.
    Returns errormessage and status code if not."""
    err_msg = 'Requests must not contain more than {} recommendations per user.'
    err_msg = err_msg.format(app.config['MAX_RECOMMENDATION_ARTICLES'])

    for recs in json.values():
        if len(recs) > app.config['MAX_RECOMMENDATION_ARTICLES']:
            return err_msg, 400


def contains_ineligible_articles(json):
    """Returns false if all articles are eligible for recommendation.
    Returns errormessage and status code if not."""
    article_ids = [article['article_id'] for user in json.values() for article
                   in user]
    if len(article_ids) is 0:
        return 'No articles submitted.', 400
    not_found_articles = db.checkArticlesExists(article_ids)
    if len(not_found_articles) > 0:
        return 'Could not find articles with ids: %s.' % ', '.join(
            not_found_articles), 400

    today = datetime.utcnow().strftime('%Y/%m/%d')
    articles_today = db.getArticleIDs(today)['article_ids']
    articles_not_today = (
            set(articles_today) & set(article_ids) ^ set(article_ids))
    if articles_not_today:
        return 'These articles are not from today\'s batch: %s.' % ', '.join(
            articles_not_today), 400
    return False


def score_is_not_float(json):
    """Returns false if all scores are float numbers.
    Returns errormessage and status code if not."""
    for recommendations in json.values():
        for rec in recommendations:
            try:
                float(rec['score'])
            except ValueError:
                return 'Score must be a float', 400
    return False


def missing_explanation(json):
    """Returns false if all recommendations have an explanation.
    Returns errormessage and status code if not."""
    for recommendations in json.values():
        for rec in recommendations:
            if 'explanation' not in rec:
                return 'Recommendations must include explanation.', 400
    return False


def too_long_explanation(json):
    """Returns false if all explanations are shorter than the limit.
    Returns errormessage and status code if not."""
    for recommendations in json.values():
        for rec in recommendations:
            if len(rec['explanation']) > app.config['MAX_EXPLANATION_LEN']:
                return 'Explanations must be shorter than %s.' % app.config[
                    'MAX_EXPLANATION_LEN'], 400
    return False
