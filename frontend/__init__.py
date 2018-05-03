# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import json
import os
from mail import mailServer
with open(os.path.dirname(__file__)+'/../config.json', 'r') as f:
    config = json.load(f)
    jwtKey = config.get('frontend_config').get('jwt_key')
    secret_key = config.get('frontend_config').get('secret_key')
path = os.path.join(os.path.dirname(__file__), 'templates')
mailServer = mailServer(**config.get('email_configuration'), templates=path)
