# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from functools import wraps
from flask import render_template, g, request, make_response, jsonify
from uuid import UUID
from api.config import APIconfig
import api.database as db


def validateApiKey(f):
    """Decorator for validating API keys. If the API key is invalid it will return 401 to the client,
    else it will store information about the system in g."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get('api_key', '')
        try:
            UUID(key, version=4)
        except ValueError:
            return make_response(jsonify({'error': 'Malformed API key.'}), 401)
        system = db.getSystem(key)
        if system is None:
            return make_response(jsonify({'error': 'Invalid API key.'}), 401)
        if not system['active']:
            return make_response(jsonify({'error': 'System is inactive.'}), 401)
        g.apiKey = system['api_key']
        g.sysName = system['system_name']
        g.sysID = system['system_ID']
        return f(*args, **kwargs)

    return wrapper


def getUserlist(f):
    """Decorator for getting user IDs from url, and validating them."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            ids = request.args.get('user_id').split(',')
        except:
            return make_response(jsonify({'error': 'No IDs supplied.'}, 400))
        if not all([x.isdigit() and int(x) > 0 for x in ids]):  # checks that all ids are valid
            return make_response(jsonify({'error': 'Invalid ids.'}), 400)
        if len(ids) > APIconfig['MAX_USERINFO_REQUEST']:
            err = 'You cannot request more than %s users at a time.' % APIconfig[
                'MAX_USERINFO_REQUEST']
            return make_response(jsonify({'error': err}), 400)

        users = db.checkUsersExists(ids)
        if len(users) > 0:
            err = 'No users with ids: %s.' % ', '.join(users)
            return make_response(jsonify({'error': err}), 400)
        kwargs['users'] = ids
        return f(*args, **kwargs)

    return wrapper
