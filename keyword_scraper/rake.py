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
    """To change the scoring fuctions, use the Metric class provied.
    Example of a Rake initialization can be
        r = Rake(max_lenght=4, scoring_metric=Metric.WORD_FREQUENCY)

    WORD_FREQUENCY favors words that appear more frequent
    WORD_DEGREE favors words that occur often and in longer keywords
    DEGREE_TO_FREQUENCY_RATIO favours words that mostly occur in longer keywords"""

    def __init__(self, max_length,
                 scoring_metric=Metric.DEGREE_TO_FREQUENCY_RATIO,
                 stopwords=nltk.corpus.stopwords.words('english'),
                 punctuation=string.punctuation.replace('-', ''),
                 min_occurrences=2,
                 min_char_length=5,
                 min_chars=5):
        """Initializes a rake object with english stop words and string punctuations."""
        self.stopwords = set(stopwords)
        self.punctuations = punctuation
        self.max_length = max_length
        self.scoring_metric = scoring_metric
        self.min_occurrences = min_occurrences
        self.min_char_length = min_char_length
        self.min_chars = min_chars
        self.frequency = None
        self.degree = None
        self.rank_list = None
        self.ranked_phrases = None

    def extract_keyword_from_sentences(self, sentences):
        """Extracts keywords from list of sentences."""
        phrases = defaultdict(int)
        adjoined_phrases = defaultdict(int)
        for i, sentence in enumerate(sentences):
            if i % 1000 == 0:
                print('\rProcessed {} sentences.'.format(i), end='')

            word_list = word_tokenize(sentence.lower())

            for phrase in self.__get_candidate_keywords(word_list):
                phrases[phrase] += 1

            for phrase in self.__adjoined_candidates_from_sentence(word_list):
                adjoined_phrases[phrase] += 1

        for phrase, count in adjoined_phrases.items():
            phrases[phrase] += count if count >= self.min_occurrences else 0

        phrases = {k: c for k, c in phrases.items() if self.__valid_keyword(k)}

        self.frequency = self.__create_freq_dist(phrases)
        self.degree = self.__create_degree_dist(phrases)
        self.__find_ranked_keywords(phrases)

    def __valid_keyword(self, keyword):
        if len(keyword) < self.min_char_length:
            return False
        if sum(c.isalpha() for c in keyword) < self.min_chars:
            return False
        return True

    def __get_candidate_keywords(self, word_list):
        """Returns candidate keywords for a tokenized sentence."""
        candidates = []
        current_candidate = []

        for word in word_list:
            if word not in self.stopwords and word not in self.punctuations:
                current_candidate.append(word)
            elif current_candidate:
                candidates.append(current_candidate)
                current_candidate = []
        if current_candidate:
            candidates.append(current_candidate)

        return [' '.join(k) for k in candidates if len(k) <= self.max_length]

    def __adjoined_candidates_from_sentence(self, word_list):
        """Finds all candidates for adjoined keywords in a sentence."""
        candidates = []
        for ngram in extract_ngrams(word_list, 2, self.max_length):
            in_stopwords = [1 if w in self.stopwords else 0 for w in ngram]
            if not any(in_stopwords[1:-1]):
                continue  # If ngram no internal stopwords
            if in_stopwords[0] or in_stopwords[-1]:
                continue  # If ngram starts or stops with a stopword
            if any([1 for w in ngram if w in self.punctuations]):
                continue  # If ngram contains punctuation
            candidates.append(' '.join(ngram))
        return candidates

    def get_all_candidate_keywords_for_sentence(self, sentence):
        """This function returns all the candidate keywords considered for a
        sentence when extracting keywords."""
        word_list = word_tokenize(sentence.lower())
        candidates = self.__get_candidate_keywords(word_list)
        return candidates + self.__adjoined_candidates_from_sentence(word_list)

    def __create_freq_dist(self, phrase_list):
        """Computes the word frequency by counting the occurence
        of single word in all phrases."""
        frequency = Counter()
        for phrase in phrase_list:
            tokenized_phrase = word_tokenize(phrase)
            for word in tokenized_phrase:
                frequency[word] += phrase_list[phrase]
        return frequency

    def __create_degree_dist(self, phrase_list):
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

    def __find_ranked_keywords(self, phrase_list):
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
                    raise ValueError(
                        'Invalid Metric: {}'.format(self.scoring_metric))
            self.rank_list.append((rank, ' '.join(phrase)))
        self.rank_list.sort(reverse=True)
        self.ranked_phrases = [phrase[1] for phrase in self.rank_list]

    def get_keywords(self):
        """"Returns the candidate keywords created"""
        return self.ranked_phrases

    def get_keywords_with_score(self):
        """Returns the candidate keywords created together with their score"""
        return self.rank_list


def extract_ngrams(word_list, n_min, n_max):
    """Returns ngrams from the text with lengths between n_min and n_max."""
    n_grams = []
    for n in range(n_min, n_max + 1):
        n_grams.extend(ngrams(word_list, n))
    return n_grams
