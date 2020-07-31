# -*- coding: utf-8 -*-
"""This script gathers category names from 'https://arxiv.org/category_taxonomy'
If problems occur gathering names one may
also consider 'https://arxiv.org/help/api/user-manual#subject_classifications'
"""

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import logging
import re

import requests
from bs4 import BeautifulSoup

ARXIV_CATEGORY_TAXONOMY_URL = 'https://arxiv.org/category_taxonomy'

# Write category names in this dictionary to override the automatically
# scraped names. These will also be used as a backup if scraping fails.
OVERRIDE_CATEGORIES = {}

def get_categories(url):
    """Find all arXiv categories on the arXiv category page.
    :param url: Url for arXiv categegory page.
    :return: Dict of catgory_id: category_name pairs.
    """
    try:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.content, "html.parser")
        category_list = soup.find(id="category_taxonomy_list")
        category_elements = category_list.findChildren("h4", recursive=True)
    except Exception as e:
        category_elements = []
        logging.exception(e)

    categories = {}
    for category in category_elements:
        match = re.search(r'([,\w\- ]+\.[,\w\- ]+) \((.+)\)',
                          category.text)
        if match:
            categories[match[1]] = match[2].strip()
    if not categories:
        print('No categories found, this could be caused by arxiv.com',
              'changing their category website.')
    categories.update(OVERRIDE_CATEGORIES)
    return categories


sub_category_names = get_categories(ARXIV_CATEGORY_TAXONOMY_URL)

