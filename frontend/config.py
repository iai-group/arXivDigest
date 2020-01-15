# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import json
import os

with open(os.path.dirname(__file__) + '/../config.json', 'r') as f:
    config = json.load(f)
    frontend_config = config.get('frontend_config')
    config['email_configuration']['templates'] = os.path.join(
        os.path.dirname(__file__), 'templates')
    jwtKey = frontend_config.get('jwt_key')
    secret_key = frontend_config.get('secret_key')
