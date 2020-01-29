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

with open('../config.json', 'r') as f:
    config = json.load(f)
    scraper_dblp_config = config.get('scraper_dblp_config')
    dump_url = scraper_dblp_config.get('dblp_dump_link')
    dump_file_path = scraper_dblp_config.get('dblp_save_path')
    keyword_lenght = scraper_dblp_config.get('max_keyword_length')

try:
    import rake
except:
    sys.path.append(os.path.abspath('../scripts/'))
from scripts.rake import Rake
from scripts.rake import Metric

def download_dump(dump_url, dump_path):
    """Downloads a dblp dump file to disk."""
    print('Downloads dblp dump to file')
    try:
        document = requests.get(dump_url)
    except Exception as e:
        return e

    with open(dump_path,'wb') as outFile:
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
    Return keyword and score in nested lists."""
    print('Creates keywords from dumped titles')
    r = Rake(keyword_lenght, Metric.WORD_FREQUENCY)
    r.extract_keyword_from_sentences(titles)
    rank_list = r.get_keywords_with_score()
    new_keywords = {}
    for score, word in rank_list:
        if not bool(re.search(r'\d', word)): 
            new_keywords[word] = score
    return new_keywords

def match_keywords(conn, titles, keywords, keyword_lenght):
    """Matches the titles with which of the created keywords they
    contain. Then inserts them into the database."""
    print('Matches keywords to titles and inserts into db.')
    for title in titles:
        candidate_keywords = create_ngram_list(title, keyword_lenght)
        title_keywords = {}
        for candidate_keyword in candidate_keywords:
            if candidate_keyword in keywords:
                title_keywords[candidate_keyword] = keywords[candidate_keyword]
        database_insert_keywords(conn, title, title_keywords)
        

def database_insert_keywords(conn, title, keywords):
    """Inserts keywords and scores into the database for each title."""
    cur = conn.cursor()
    keywords_query = 'insert ignore into keywords values (%s,%s,%s)'
    for keyword in keywords:
        data = [title, keyword, keywords[keyword]]
        cur.execute(keywords_query, data)
    conn.commit()
    cur.close()

def create_ngram_list(title, keyword_lenght):
    """Creates a list of all possible keywords for a paper title using ngrams."""
    stopwords = nltk.corpus.stopwords.words('english')
    punctuations = string.punctuation.replace('-', '')
    candidate_keywords = []
    for i in range(1,keyword_lenght):
        ngrams = extract_ngrams(title, i)
        for gram in ngrams:
            if word_tokenize(gram)[0] in stopwords or word_tokenize(gram)[-1] in stopwords:
                continue
            elif word_tokenize(gram)[0] in punctuations or word_tokenize(gram)[-1] in punctuations:
                continue
            else:
                candidate_keywords.append(gram.lower())
    return candidate_keywords

def extract_ngrams(data, num):
    """Returns ngrams from data with length specified by the number supplied."""
    n_grams = ngrams(nltk.word_tokenize(data), num)
    return [' '.join(grams) for grams in n_grams]

def clear_keyword_database(conn):
    """Clears keyword table in database for titles and keywords."""
    cur = conn.cursor()
    clear_sql = 'DELETE FROM keywords;'
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