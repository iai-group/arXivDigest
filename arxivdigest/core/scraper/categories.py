# -*- coding: utf-8 -*-
"""This script gathers category names from 'https://arxiv.org/category_taxonomy'
If problems occur gathering names one may
also consider 'https://arxiv.org/help/api/user-manual#subject_classifications'
"""

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import re

import requests
from bs4 import BeautifulSoup

ARXIV_CATEGORY_TAXONOMY_URL = 'https://arxiv.org/category_taxonomy'


def get_categories(url):
    """Find all arXiv categories on the arXiv category page.
    :param url: Url for arXiv categegory page.
    :return: Dict of catgory_id: category_name pairs.
    """
    resp = requests.get(url)
    soup = BeautifulSoup(resp.content, "html.parser")
    soup.find(id="guide").decompose()
    content = soup.find(id='content')
    cats = content.find_all('li')

    categories = {}
    for c in cats:
        category = c.find('strong').text if c.find('strong') else c.text
        match = re.search(r'([,\w\- ]+) (\(.+\))', category)
        if match:
            category_name = re.sub('[()]', '', match[2])
            categories[category_name] = match[1].strip()
    if not categories:
        print('No categories found, this could be caused by arxiv.com',
              'changing their category website.')
    return categories


sub_category_names = get_categories(ARXIV_CATEGORY_TAXONOMY_URL)
