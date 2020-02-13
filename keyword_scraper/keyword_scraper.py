# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2020, The ArXivDigest Project"

from mysql import connector
import gzip
import re
import requests
import nltk
import string
from nltk.tokenize import word_tokenize
import json
from nltk.util import ngrams
import sys
import os
from rake import Rake
from rake import Metric

with open(os.path.dirname(__file__) + '/../config.json', 'r') as f:
    config = json.load(f)
    scraper_dblp_config = config.get('keyword_scraper_config')
    dump_url = scraper_dblp_config.get('dblp_dump_link')
    dump_file_path = scraper_dblp_config.get('dblp_save_path')
    keyword_lenght = scraper_dblp_config.get('max_keyword_length')


def download_dump(dump_url, dump_path):
    """Downloads a dblp dump file to disk."""
    print('Downloading dblp dump to file')
    try:
        document = requests.get(dump_url)
    except Exception as e:
        return e

    with open(dump_path, 'wb') as outFile:
        outFile.write(document.content)


def find_dblp_titles(file_path):
    """Scrapes the dbpl xml dump file for publicated titles
    and returns all titles in a list."""
    print('Scrapes dblp dump for paper titles')
    titles = []
    with gzip.open(file_path, 'rt') as f:
        for line in f:
            if line.startswith('<title>'):
                line = re.sub('<title>', '', line)
                line = re.sub('</title>', '', line)
                line = re.sub('\n', '', line)
                titles.append(line)
    return titles


def find_dblp_keywords(titles, keyword_lenght):
    """Uses rake to find keywords for set of all dblp titles.
    Return keyword and score in dictionary."""
    print('Creates keywords from dumped titles')
    r = Rake(keyword_lenght, Metric.WORD_FREQUENCY)
    r.extract_keyword_from_sentences(titles)
    rank_list = r.get_keywords_with_score()
    new_keywords = {}
    for score, word in rank_list:
        if len(word) < 75:
            new_keywords[word] = score
    return new_keywords


def match_keywords(conn, titles, keywords, keyword_lenght, batch_size=1000):
    """Matches the titles with which of the created keywords they
    contain. Then inserts them into the database."""
    print('\nMatches keywords to titles and inserts into db.')
    r = Rake(keyword_lenght, Metric.DEGREE_TO_FREQUENCY_RATIO,
             min_occurrences=10)
    for i in range(0, len(titles), batch_size):
        print('\rProcessed {} titles.'.format(i), end='')
        match_keyword_batch(conn, titles[i:i + batch_size], keywords, r)


def match_keyword_batch(conn, titles, keywords, rake):
    title_keywords = []
    for title in titles:
        candidate_keywords = rake.get_all_candidate_keywords_for_sentence(title)
        for keyword in candidate_keywords:
            if keyword in keywords:
                title_keywords.append((title, keyword, keywords[keyword]))
    database_insert_keywords(conn, title_keywords)


def database_insert_keywords(conn, data):
    """Inserts keywords and scores into the database for each title."""
    cur = conn.cursor()
    query = 'replace into keywords (title, keyword, score) values (%s,%s,%s)'
    cur.executemany(query, data)
    conn.commit()
    cur.close()


def clear_keyword_database(conn):
    """Clears keyword table in database for titles and keywords."""
    cur = conn.cursor()
    clear_sql = 'TRUNCATE TABLE keywords;'
    cur.execute(clear_sql)
    conn.commit()
    cur.close()


if __name__ == '__main__':
    conn = connector.connect(**config.get("sql_config"))
    clear_keyword_database(conn)

    download_dump(dump_url, dump_file_path)
    titles = find_dblp_titles(dump_file_path)
    keywords = find_dblp_keywords(titles, keyword_lenght)
    match_keywords(conn, titles, keywords, keyword_lenght)

    conn.close()
