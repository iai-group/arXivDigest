# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import json
import os
from pkg_resources import resource_filename, Requirement

__file_locations = [
    os.path.expanduser('~') + '/arXivDigest/config.json',
    '/etc/arXivDigest/config.json',
    os.curdir + '/config.json',
    os.curdir + '/../../arXivDigest/config.json',
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


with open(find_config_file(__file_locations)) as file:
    config = json.load(file)

config['email_config']['templates'] = resource_filename(
    Requirement.parse('arXivDigest'), 'core/mail/templates')

sql_config = config.get('sql_config')
email_config = config.get('email_config')
api_config = config.get('api_config')
interleave_config = config.get('interleave_config')
frontend_config = config.get('frontend_config')
evaluation_config = config.get('evaluation_config')
keyword_scraper_config = config.get('keyword_scraper_config')

jwtKey = frontend_config.get('jwt_key')
secret_key = frontend_config.get('secret_key')
