# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The ArXivDigest Project'

from frontend.scrape_titles.dblp import get_dblp_titles

def find_author_titles(author_url):
    """Checks the provided link and fetches keywords from the required
    website. If site is not supported or the fetching fails, return
    empty string."""
    if 'dblp.' in author_url: 
        author_titles = get_dblp_titles(author_url)
        return author_titles
    else:
        raise ValueError('Webpage is not supported')
