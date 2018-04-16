__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from functools import wraps
from flask import render_template, g, request, make_response, jsonify
from database import getSystem
from uuid import UUID


def validateApiKey(f):
    '''Decorator for validating apikeys, if the apikey is invalid it will return 401 to the client,
    else it will store information about the system in g.'''
    @wraps(f)
    def wrapper(*args, **kwargs):
        key = request.headers.get('api_key', '')
        try:
            UUID(key, version=4)
        except ValueError:
            return make_response(jsonify({'error': 'Malformed api-key.'}), 401)
        system = getSystem(key)
        if system is None:
            return make_response(jsonify({'error': 'Invalid api-key.'}), 401)
        if not system['active']:
            return make_response(jsonify({'error': 'System is inactive.'}), 401)
        g.apiKey = system['api_key']
        g.sysName = system['system_name']
        g.sysID = system['system_ID']
        return f(*args, **kwargs)
    return wrapper
