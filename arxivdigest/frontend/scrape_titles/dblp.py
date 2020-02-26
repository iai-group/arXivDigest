# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The ArXivDigest Project'

import requests
from bs4 import BeautifulSoup

def get_pid(auth_url):
    """Returns an author dblp PID from an author dblp profile page link.
    If no response or no result from scraping the web page it returns
    an error."""
    resp = requests.get(auth_url)

    parsed_html = BeautifulSoup(resp.content, 'html.parser')
    pid_element = parsed_html.select_one(
        '#main > header > nav > ul > li.share.drop-down > div.body > ul.bullets > li > small')
    if pid_element:
        return pid_element.text
    else:
        raise ValueError('No pid adress found on author page')

def get_titles_from_pid(pid):
    """Returns a list of titles from an author using the authors PID web
    address. Returns error if the author has no titles or request fails."""
    document = requests.get(pid + '.xml')

    soup = BeautifulSoup(document.content, 'lxml')
    titles = soup.find_all('title')
    if titles:
        return [title.text for title in titles]
    else:
        raise ValueError('Author has no publicated papers')

def get_dblp_titles(author_url):
    """Fetches the author pid and then the author paper titles.
    Returns list of titles"""
    author_pid = get_pid(author_url)
    author_titles = get_titles_from_pid(author_pid)
    return author_titles
