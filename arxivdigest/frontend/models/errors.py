# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


class ValidationError(Exception):
    def __init__(self, message):
        self.message = message
