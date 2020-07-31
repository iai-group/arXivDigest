# -*- coding: utf-8 -*-
"""This module implements the methods used for storing scraped metadata
from arXiv into a mySQL database."""

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from arxivdigest.core import database
from arxivdigest.core.config import CONSTANTS
from arxivdigest.core.scraper.categories import sub_category_names
from arxivdigest.core.scraper.scrape_metadata import get_categories


def insert_into_db(metaData):
    """Inserts the supplied articles into the database.
    Duplicate articles are ignored."""
    print('Trying to insert %d elements into the database.' % len(metaData))
    conn = database.get_connection()
    cur = conn.cursor()
    try:
        insert_categories(metaData, cur)
        article_category_sql = 'insert into article_categories values(%s,%s)'

        for i, (article_id, article) in enumerate(metaData.items()):
            insert_article(cur, article_id, article)

            if cur.rowcount == 0:  # Ignore article already in database
                continue
            for category in article['categories']:
                cur.execute(article_category_sql, (article_id, category))
            for author in article['authors']:
                insert_author(cur, article_id, author['firstname'],
                              author['lastname'], author['affiliations'])

            conn.commit()
            print('\rInserted {} elements.'.format(i), end='')
        print('\nSuccessfully inserted the elements.')
    finally:
        cur.close()
        conn.close()


def truncate_value(value, max_length):
    err_msg = 'Value: {} was to long for column and was truncated to {}.'
    if value and len(value) > max_length:
        old_value = value
        value = value[:CONSTANTS.max_human_name_length]
        print(err_msg.format(old_value, value))
    return value


def insert_article(cur, article_id, article):
    """Inserts article into articles table."""
    sql = 'INSERT IGNORE INTO articles VALUES(%s,%s,%s,%s,%s,%s,%s,%s)'
    title = truncate_value(article['title'], CONSTANTS.max_title_length)
    journal = truncate_value(article['journal'], CONSTANTS.max_journal_length)
    license = truncate_value(article['license'], CONSTANTS.max_license_length)

    data = [article_id, title, article['description'], article['doi'],
            article['comments'], license, journal, article['datestamp']]
    cur.execute(sql, data)


def insert_author(cur, article_id, firstname, lastname, affiliations):
    """Inserts author into authors table."""

    sql = 'INSERT INTO article_authors VALUES(null,%s,%s,%s)'
    firstname = truncate_value(firstname, CONSTANTS.max_human_name_length)
    lastname = truncate_value(lastname, CONSTANTS.max_human_name_length)

    cur.execute(sql, (article_id, firstname, lastname))
    insert_affiliations(cur, cur.lastrowid, affiliations)


def insert_affiliations(cur, author_id, affiliations):
    """Inserts affiliations for author into author_affiliations."""
    sql = 'INSERT INTO author_affiliations VALUES(%s,%s)'
    data = []
    for affiliation in affiliations:
        affiliation = truncate_value(affiliation,
                                     CONSTANTS.max_affiliation_length)
        if affiliation:
            data.append((author_id, affiliation))
    cur.executemany(sql, data)


def insert_categories(metaData, cursor):
    """Inserts all categories from the metaData into the database"""
    categories = set()
    categoryNames = get_categories()
    for value in metaData.values():
        for category in value['categories']:
            c = category.split('.')

            try:
                categoryName = categoryNames[c[0]]['name']
            except KeyError:
                categoryName = c[0]
                print(
                    'Update category name manually: could not find name for %s' % c[0])
            name = categoryName
            if len(c) > 1:
                try:
                    subcategoryName = sub_category_names[category]
                    name += '.' + subcategoryName
                except KeyError:
                    print('Could not find name for category: %s.' % category)
            # add both main category and sub category to database
            categories.add((c[0], c[0], None, categoryName))
            if len(c) > 1:
                categories.add((category, c[0], (c[1:] + [None])[0], name))

    sql = 'replace into categories values(%s,%s,%s,%s)'
    cursor.executemany(sql, list(categories))
