# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2020, The ArXivDigest Project"

import nltk
import string
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict
import re

class Rake(object):
    def __init__(self,max_length,scoring_metric):
        '''Initializes a rake object with english stop words and string punctuations.
        Must define max_lenth and what scoring metric to use.
        Scoring metrics avaiable are f, d, df.'''
        self.stopwords=nltk.corpus.stopwords.words('english') 
        self.punctuations = string.punctuation.replace('-','')
        self.max_length = max_length
        self.scoring_metric = scoring_metric
        self.frequency = None
        self.degree = None
        self.rank_list = None
        self.ranked_phrases = None
    
    def extract_keyword_from_title_list(self, title_list):
        '''Extracts keywords from list of paper titles.'''
        phrase_list = set()
        for title in title_list:
            word_list = [word.lower() for word in word_tokenize(title)]
            phrase_list.update(self.get_candidate_keywords(word_list))
        self.create_freq_dist(phrase_list)
        self.create_degree_dist(phrase_list)
        self.find_ranked_keywords(phrase_list)
    
    def get_candidate_keywords(self, tokenized_title):
        '''Returns candidate keywords for a tokenized title.'''
        candidate_keywords = []
        current_candidate = ''
        for word in tokenized_title:
            if word not in self.stopwords and word not in self.punctuations:
                current_candidate += word + ' '
            elif current_candidate != '':
                candidate_keywords.append(current_candidate[:-1])
                current_candidate = ''
        if current_candidate != '':
            candidate_keywords.append(current_candidate[:-1])
        filtered_keyword = []
        for keyword in candidate_keywords:
            if len(word_tokenize(keyword)) <= self.max_length:
                filtered_keyword.append(keyword)
        return filtered_keyword
    
    def create_freq_dist(self, phrase_list):
        '''Computes the word frequency by counting the occurence
        of single word in all phrases.'''
        self.frequency = Counter()
        for phrase in phrase_list:
            phrase = word_tokenize(phrase)
            for word in phrase:
                self.frequency[word] += 1 
        
    def create_degree_dist(self, phrase_list):
        '''Computes the word degree of each single word in each 
        phrase.'''
        co_occurence_graph = defaultdict(lambda: defaultdict(lambda: 0))
        for phrase in phrase_list:
            phrase = word_tokenize(phrase)
            for word in phrase:
                for co_word in phrase:
                    co_occurence_graph[word][co_word] += 1
        self.degree = defaultdict(lambda: 0)
        for word in co_occurence_graph:
            self.degree[word] = sum(co_occurence_graph[word].values())
    
    def find_ranked_keywords(self, phrase_list):
        '''Ranks the keywords found using degree/freq.'''
        self.rank_list = []
        for phrase in phrase_list:
            rank = 0.0
            phrase = word_tokenize(phrase)
            for word in phrase:
                if self.scoring_metric == 'df':
                    rank += 1.0 * self.degree[word] / self.frequency[word]
                elif self.scoring_metric == 'f':
                    rank += 1.0 * self.frequency[word]
                else:
                    rank += 1.0 * self.degree[words]
            self.rank_list.append((rank, " ".join(phrase)))
        self.rank_list.sort(reverse=True)
        self.ranked_phrases = [phrase[1] for phrase in self.rank_list]

def load_stopwords(path):
    '''Loads stopwords from a file. File must have one stop word
    per line and no first line explanation or title.'''
    stopwords = []
    for line in open(path):
        stopwords.append(re.sub('\n', '', line))
    return stopwords