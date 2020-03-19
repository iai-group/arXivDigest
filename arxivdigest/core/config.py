# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import json
import os
import sys

__file_locations = [
    os.path.expanduser('~') + '/arxivdigest/config.json',
    '/etc/arxivdigest/config.json',
    os.curdir + '/config.json',
]


def find_config_file(file_locations):
    """Checks the given list of file paths for a config file,
    returns None if not found."""
    for file_location in file_locations:
        if os.path.isfile(file_location):
            print('Found config file at: {}'.format(
                os.path.abspath(file_location)))
            return file_location
    return None


config_file = find_config_file(__file_locations)
if not config_file:
    print('No config-file found in any of the following locations:')
    for location in __file_locations:
        print(os.path.abspath(location))
    print('Exiting.')
    sys.exit()

with open(config_file) as file:
    config = json.load(file)

config_web_address = config.get('web_address')
config_sql = config.get('sql_config')
config_email = config.get('email_config')
config_api = config.get('api_config')
config_interleave = config.get('interleave_config')
config_frontend = config.get('frontend_config')
config_evaluation = config.get('evaluation_config')

jwtKey = config_frontend.get('jwt_key')
secret_key = config_frontend.get('secret_key')
