# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import jwt
import math
import datetime
import frontend.database.admin as admin
from functools import wraps
from flask import g, request, make_response, redirect, url_for
from frontend.config import config, jwtKey


def requiresLogin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        '''Decorator to use before paths where users must be logged in to access. Checks if users are logged in.'''
        if g.loggedIn:
            return f(*args, **kwargs)
        else:
            return make_response(redirect(url_for('general.loginPage', next=request.full_path)))
    return wrapper


def encode_auth_token(id, email):
    '''Creates authToken for user with id and email with expire time of 10 days'''
    payload = {
        'exp': datetime.datetime.now() + datetime.timedelta(days=10),
        'sub': id,
        'admin': admin.isAdmin(id),
        'email': email
    }
    return jwt.encode(payload, jwtKey, algorithm='HS256').decode()


def pageinate(page, maxPage, n):
    '''Helperfunction for making a pageselector, page is the current page,
    maxPage is the last page and n is the number of pages to show in the pageselector.'''
    pages = [page]
    min = page-1
    max = page+1
    while len(pages) < n:
        if (2*page-min <= max or max >= maxPage)and min > 0:
            pages.append(min)
            min -= 1
        elif max <= maxPage:
            pages.append(max)
            max += 1
        else:
            break
    pages = sorted(pages)
    if maxPage > n and n > 5:
        if pages[0] != 1:
            pages[0] = 1
            pages[1] = -1
        if pages[-1] != maxPage:
            pages[-1] = maxPage
            pages[-2] = -1
    return pages
