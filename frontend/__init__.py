__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import json
import os
with open(os.path.dirname(__file__)+'/../config.json', 'r') as f:
    config = json.load(f)
    jwtKey = config.get('frontend_config').get('jwt_key')
