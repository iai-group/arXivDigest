# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"


class ValidationError(Exception):
    def __init__(self, message, code):
        self.code = code
        self.message = message
