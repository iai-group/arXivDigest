# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"


import re


def validEmail(email):
    '''Checks if email is valid email format, returns true if valid, false if not.'''
    return re.match('^[a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$', email) is not None


def validPassword(password):
    '''Returns tue if password is valid, false if invalid.'''
    return re.match('(?=^.{9,256}$)(?=.*\d)(?=.*\W+)(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$', password) is not None


def validString(string, minLength, maxLength):
    if not isinstance(string, str) or len(string) < minLength or len(string) > maxLength:
        return False
    return True
