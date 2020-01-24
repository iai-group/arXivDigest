# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2020, The ArXivDigest Project"

import nltk
import string
from nltk.tokenize import word_tokenize
from collections import Counter, defaultdict
import re
from nltk.util import ngrams
from enum import Enum


class Metric(Enum):
    """Different metrics that can be used for ranking candidate keywords."""
    DEGREE_TO_FREQUENCY_RATIO = 0  
    WORD_DEGREE = 1 
    WORD_FREQUENCY = 2  


class Rake(object):
    def __init__(self, max_length, scoring_metric=Metric.DEGREE_TO_FREQUENCY_RATIO, stopwords=None, punctuation=None):
        """Initializes a rake object with english stop words and string punctuations.
        Must define max_lenth and what scoring metric to use.
        Scoring metrics available are f, d, df."""
        self.stopwords = stopwords if stopwords else nltk.corpus.stopwords.words('english')
        self.punctuations = punctuation if punctuation else string.punctuation.replace('-', '')
        self.max_length = max_length
        self.scoring_metric = scoring_metric
        self.frequency = None
        self.degree = None
        self.rank_list = None 
        self.ranked_phrases = None

    def extract_keyword_from_sentences(self, sentences): 
        """Extracts keywords from list of sentences."""
        phrase_list = Counter()  #TODO prob not set
        for sentence in sentences:
            word_list = [word.lower() for word in word_tokenize(sentence)]
            phrase_list = phrase_list + Counter(self.get_candidate_keywords(word_list))
        phrase_list = phrase_list + Counter(self.find_adjoining_keywords(sentences))
        self.frequency = self.create_freq_dist(phrase_list)
        self.degree = self.create_degree_dist(phrase_list)
        self.find_ranked_keywords(phrase_list)

    def get_candidate_keywords(self, tokenized_sentence):
        """Returns candidate keywords for a tokenized sentence."""
        candidate_keywords = []
        current_candidate = ''
        for word in tokenized_sentence:
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

    def find_adjoining_keywords(self, titles):
        """Finds adjoining keywords from list of all paper titles"""
        title_data = ''
        for title in titles:
            title_data += title + ' '
        adjoining_keywords = Counter()
        for i in range(self.max_length):
            adjoining_keywords = adjoining_keywords + Counter(extract_ngrams(title_data, i + 1))
        filtered_keywords = []
        for keyword, count in adjoining_keywords.items():
            if count < 3 or keyword in self.stopwords or keyword in self.punctuations:
                continue
            if word_tokenize(keyword)[0] in self.stopwords or word_tokenize(keyword)[-1] in self.stopwords:
                continue
            if word_tokenize(keyword)[0] in self.punctuations or word_tokenize(keyword)[-1] in self.punctuations:
                continue
            if len(word_tokenize(keyword)) <= self.max_length:
                filtered_keywords.append(keyword)
        return filtered_keywords

    def create_freq_dist(self, phrase_list):
        """Computes the word frequency by counting the occurence
        of single word in all phrases."""
        frequency = Counter() 
        for phrase in phrase_list:
            tokenized_phrase = word_tokenize(phrase)
            for word in tokenized_phrase:
                frequency[word] += phrase_list[phrase] 
        return frequency

    def create_degree_dist(self, phrase_list):
        """Computes the word degree of each single word in each
        phrase."""
        co_occurence_graph = defaultdict(lambda: defaultdict(lambda: 0))
        for phrase in phrase_list:
            tokenized_phrase = word_tokenize(phrase)
            for word in tokenized_phrase:
                for co_word in tokenized_phrase:
                    co_occurence_graph[word][co_word] += phrase_list[phrase]
        degree = defaultdict(lambda: 0) 
        for word in co_occurence_graph:
            degree[word] = sum(co_occurence_graph[word].values())
        return degree

    def find_ranked_keywords(self, phrase_list):
        """Ranks the keywords found using the specified scoring metric"""
        self.rank_list = []
        for phrase in phrase_list:
            rank = 0.0
            phrase = word_tokenize(phrase)
            for word in phrase:
                if self.scoring_metric == Metric.DEGREE_TO_FREQUENCY_RATIO:
                    rank += 1.0 * self.degree[word] / self.frequency[word]
                elif self.scoring_metric == Metric.WORD_FREQUENCY:
                    rank += 1.0 * self.frequency[word]
                elif self.scoring_metric == Metric.WORD_DEGREE:
                    rank += 1.0 * self.degree[word]
                else:
                   raise ValueError('Invalid Metric: {}'.format(self.scoring_metric))
            self.rank_list.append((rank, ' '.join(phrase)))
        self.rank_list.sort(reverse=True)
        self.ranked_phrases = [phrase[1] for phrase in self.rank_list]
    
    def get_keywords(self):
        """"Returns the candidate keywords created"""
        return self.ranked_phrases

    def get_keywords_with_score(self):
        """Returns the candidate keywords created together with their score"""
        return self.rank_list


def load_stopwords(path):
    """Loads stopwords from a file. File must have one stop word
    per line and no first line explanation or title."""
    stopwords = []
    for line in open(path):
        stopwords.append(re.sub('\n', '', line))
    return stopwords


def extract_ngrams(data, num):
    """Returns ngrams from data with length specified by the number supplied"""
    n_grams = ngrams(nltk.word_tokenize(data), num)
    return [' '.join(grams) for grams in n_grams]
