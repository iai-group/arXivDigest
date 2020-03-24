# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import datetime
import gzip
from functools import wraps
from uuid import uuid4

import jwt
from flask import g
from flask import make_response
from flask import redirect
from flask import request
from flask import url_for

import arxivdigest.frontend.database.admin as admin
import arxivdigest.frontend.database.general as general
from arxivdigest.core.config import jwtKey
from arxivdigest.core.config import config_email
from arxivdigest.core.mail.mail_server import MailServer
from arxivdigest.core.config import config_web_address


def requiresLogin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        """Decorator to use before paths where users must be logged in to access.
         Checks if users are logged in and redirects to login page if not."""
        if g.inactive:
            return make_response(redirect(url_for('general.confirm_email_page',
                                                  next=request.script_root + request.full_path)))
        elif g.loggedIn:
            return f(*args, **kwargs)
        else:
            return make_response(redirect(url_for('general.loginPage',
                                                  next=request.script_root + request.full_path)))
    return wrapper


def encode_auth_token(id, email):
    """Creates authToken for user with id and email with expire time of 10 days"""
    payload = {
        'exp': datetime.datetime.now() + datetime.timedelta(days=10),
        'sub': id,
        'admin': admin.isAdmin(id),
        'email': email,
        'inactive': general.is_activated(id)
    }
    return jwt.encode(payload, jwtKey, algorithm='HS256').decode()


def pageinate(page, maxPage, n):
    """Helperfunction for making a pageselector, page is the current page,
    maxPage is the last page and n is the number of pages to show in the pageselector."""
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


def create_gzip_response(content_bytes, filename):
    """Creates gzip-file from the 'content_bytes' with the name 'filename'
    inside a flask response object.

    :param content_bytes: Bytes that will be gziped.
    :param filename: The name of the downloadable gzip file.
    :return: Response object with downloadable gzip-file.
    """
    response = make_response()
    response.set_data(gzip.compress(content_bytes))
    response.headers['Content-Disposition'] = 'attachment;filename=' + filename
    return response

def send_confirmation_email(email):
    """Sends an email to the user to confirm their email."""
    server = MailServer(**config_email)

    trace = str(uuid4())
    mail_content = {'to_address': email,
                    'subject': 'arXivDigest email confirmation',
                    'template': 'confirm_email',
                    'data': {'activate_link': '%semail_confirm/%s'  % (config_web_address, trace),
                             'link': config_web_address}}

    general.add_activate_trace(trace, email)
    server.send_mail(**mail_content)
    server.close()