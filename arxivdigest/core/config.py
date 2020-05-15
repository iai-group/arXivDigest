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
    
_base_url = config.get('web_address')

config_web_address = _base_url if _base_url.endswith('/') else _base_url + '/'
config_sql = config.get('sql_config')
config_email = config.get('email_config')
config_api = config.get('api_config')
config_interleave = config.get('interleave_config')
config_frontend = config.get('frontend_config')
config_evaluation = config.get('evaluation_config')
config_arxiv_scraper = config.get('arxiv_scraper_config')

jwtKey = config_frontend.get('jwt_key')
secret_key = config_frontend.get('secret_key')


class Constants:
    """This class contains constants that are not configurable."""

    def __init__(self):
        # General
        self.max_human_name_length = 60
        self.max_system_name_length = 40
        self.max_email_length = 60
        self.max_url_length = 120
        self.min_url_length = 5

        # Users
        self.min_topics_per_user = 3
        self.max_organization_length = 100

        # Topics
        self.max_topic_length = 50

        # Articles
        self.max_title_length = 300
        self.max_journal_length = 300
        self.max_license_length = 120
        self.max_affiliation_length = 300


CONSTANTS = Constants()
