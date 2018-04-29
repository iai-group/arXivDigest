'''This module implements the methods used for storing the scraped metadata into the mySQL database.
InsertIntoDB() will insert all the articles in the supplied data, if an article already exists in the database
it will be overwriten.'''

_author_ = "Øyvind Jekteberg and Kristian Gingstad"
_copyright_ = "Copyright 2018, The ArXivDigest Project"

from scrapeMetadata import getCategories, harvestMetadataRss
from categories import subCategoryNames
from mysql import connector
import json

with open('../config.json', 'r') as f:
    config = json.load(f)


def insertIntoDB(metaData, conn):
    '''Inserts the supplied articles into the database.'''
    print('Trying to insert %d elements into the database.' % len(metaData))

    try:
        cur = conn.cursor()
        i = 0
        insertCategories(metaData, cur)
        # if article already exists in the database it will be overwritten with the new version
        articlestmt = 'replace into articles values(%s,%s,%s,%s,%s,%s,%s,%s)'
        articlecategorystmt = 'insert into article_categories values(%s,%s)'
        authorstmt = 'insert into article_authors values(null,%s,%s,%s)'
        affiliationstmt = 'insert into author_affiliations values(%s,%s)'

        for id, value in metaData.items():
            data = [id, value['title'], value['description'], value['doi'],
                    value['comments'], value['license'], value['journal'], value['datestamp']]
            cur.execute(articlestmt, data)
            for category in value['categories']:
                cur.execute(articlecategorystmt, (id, category))
            for author in value['authors']:
                cur.execute(
                    authorstmt, (id, author['firstname'], author['lastname']))
                authorId = cur.lastrowid
                for affiliation in author['affiliations']:
                    cur.execute(affiliationstmt, (authorId, affiliation))
            conn.commit()
            i += 1
            print('\rInserted {} elements.'.format(i), end='')
        print('Successfully inserted the elements.')
    finally:
        cur.close()
        conn.close()


def insertCategories(metaData, cursor):
    ''' Inserts all categories from the metaData into the database'''
    categories = set()
    categoryNames = getCategories()
    for value in metaData.values():
        for category in value['categories']:
            c = category.split('.')
            categoryName = categoryNames[c[0]]['name']
            # generate natural name for category
            name = categoryName
            name += '.' + subCategoryNames[category] if len(c) > 1 else ''
            # add both main category and sub category to database
            categories.add((category, c[0], (c[1:] + [None])[0], name))
            categories.add((c[0], c[0], None, categoryName))
    # fails silently on duplicate primary key, because there is
    #  no need to add the same category twice
    sql = 'insert ignore into categories values(%s,%s,%s,%s)'
    cursor.executemany(sql, categories)


if __name__ == '__main__':
    conn = connector.connect(**config.get("sql_config"))
    insertIntoDB(harvestMetadataRss(), conn)
