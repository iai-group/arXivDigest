# -*- coding: utf-8 -*-
import re


__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from functools import wraps

from flask import current_app as app
from flask import jsonify
from flask import make_response
from flask import request

import arxivdigest.api.database as db
from arxivdigest.core.config import CONSTANTS


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


def article_recommendation(json):
    """Validator function for json submitted to the recommendation insertion
    endpoint."""
    json = json.get('recommendations')
    if not json:
        return 'No recommendations submitted.', 400

    if len(json) > app.config['max_users_per_recommendation']:
        return 'Requests must not contain more than %s users.' % app.config[
            'max_users_per_recommendation'], 400

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


def topic_recommendation(json):
    """Validator function for json submitted to the topic recommendation
    endpoint."""
    json = json.get('recommendations')
    if not json:
        return 'No recommendations submitted.', 400

    if len(json) > app.config['max_users_per_recommendation']:
        return 'Requests must not contain more than %s users.' % app.config[
            'max_users_per_recommendation'], 400

    # functions that validate different properties of the json
    check_funcs = {nonexistent_users,
                   too_many_recommendations,
                   contains_ineligible_topics,
                   score_is_not_float,
                   }

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
    err_msg = err_msg.format(app.config['max_recommendations_per_user'])

    for recs in json.values():
        if len(recs) > app.config['max_recommendations_per_user']:
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

    eligible_ids = set(db.get_article_ids_past_seven_days())
    ineligible_ids = set(article_ids) - eligible_ids
    if ineligible_ids:
        return 'These articles are not from the past seven days: {}.' \
                   .format(', '.join(ineligible_ids)), 400
    return False


def contains_ineligible_topics(json):
    """Returns false if all topics are eligible for recommendation.
    Returns errormessage and status code if not."""
    topics = [topic['topic'] for user in json.values() for topic in user]
    if len(topics) is 0:
        return 'No topics submitted.', 400
    for topic in topics:
        if re.search('[^a-zA-Z0-9\- ]', topic):
            return 'Topics can only contain a..z, 0..9, space and dash.', 400
        if len(topic) > CONSTANTS.max_topic_length:
            msg = 'Topics must be shorter than {}.'
            return msg.format(CONSTANTS.max_topic_length), 400
    return False


def score_is_not_float(json):
    """Returns false if all scores are float numbers.
    Returns errormessage and status code if not."""
    for recommendations in json.values():
        for rec in recommendations:
            try:
                float(rec['score'])
            except (ValueError, KeyError):
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
            if len(rec['explanation']) > app.config['max_explanation_len']:
                return 'Explanations must be shorter than %s.' % app.config[
                    'max_explanation_len'], 400
    return False
