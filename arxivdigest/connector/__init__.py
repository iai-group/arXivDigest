# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2018, 2020, The arXivDigest project'

import logging

import requests

from arxivdigest.connector import exceptions


class ArxivdigestConnector:

    def __init__(self,
                 api_key,
                 api_url='https://api.arxivdigest.org/'):
        """Creates a ArxivdigestConnector object.

        :param api_key: A arXivDigest API key.
        :param api_url: The base url of the arXivDigest API.
        """
        self.api_key = api_key
        self.api_url = api_url if api_url.endswith('/') else api_url + '/'
        settings = self.test_connection()
        self.user_ids_per_request = settings['user_ids_per_request']
        self.max_userinfo_request = settings['max_userinfo_request']
        self.max_articledata_request = settings['max_articledata_request']
        self.users_per_recommendation = settings['max_users_per_recommendation']
        self.recommendations_per_user = settings['max_recommendations_per_user']
        self.max_explanation_len = settings['max_explanation_len']

        self.validate_api_key()

    def test_connection(self):
        """Tests the connection to the arXivDigest instance.
        :raises: connector.exceptions.ConnectionError if unable to
        establish a valid connection.
        :return: True if connected successfully
        """
        r = requests.get(self.api_url)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise exceptions.ConnectionError from e

        if r.ok and 'arXivDigest API' in r.json()['info']:
            return r.json()['settings']
        else:
            raise exceptions.ConnectionError(
                'A connection was made, but the connector '
                'was unable to verify the response was from '
                'an arXivDigest API instance.')

    def validate_api_key(self):
        """Validates the API key.
        :return: True if valid.
        :raises: exceptions.ApiKeyError If something is wrong with the API key
        """
        r = requests.get(self.api_url + 'users',
                         headers={'api-key': self.api_key})
        if r.ok:
            return True
        if 'error' in r.json():
            raise exceptions.ApiKeyError(r.json()['error'])
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise exceptions.ArxivdigestConnectorException from e
        raise exceptions.ArxivdigestConnectorException('Something unexpected '
                                                       'went wrong.')

    def get_number_of_users(self):
        """Queries the arXivDigest API for user ids.
        :return: Total number of arXivDigest users.
        """
        r = requests.get(self.api_url + 'users',
                         headers={'api-key': self.api_key})
        return r.json()['users']['num']

    def get_user_ids(self, offset=0):
        """Queries the arXivDigest API for user ids.
        :param offset: Offset to start retrieval at.
        :return: List of arXivDigest user ids sorted ascending.
        """
        r = requests.get(self.api_url + 'users', params={'from': offset},
                         headers={'api-key': self.api_key})
        return r.json()['users']['user_ids']

    def get_user_info(self, user_ids):
        """Queries the arXivDigest API for userdata for the given 'user_ids'.
        :param user_ids: List of user ids to retrieve info for.
        :return: Dictionary with user info for each user id."""
        user_info = {}
        batch_size = self.max_userinfo_request
        for i in range(0, len(user_ids), batch_size):
            id_batch = ','.join([str(u) for u in user_ids[i:i + batch_size]])
            r = requests.get(self.api_url + 'user_info',
                             params={'user_id': id_batch},
                             headers={'api-key': self.api_key})

            user_info.update(r.json()['user_info'])
        return user_info

    def get_article_ids(self):
        """Queries the arXivDigest API for article ids.
        :return: List of arXivDigest article ids.
        """
        r = requests.get(self.api_url + 'articles',
                         headers={'api-key': self.api_key})
        return r.json()['articles']

    def get_article_data(self, article_ids):
        """Queries the arXivDigest API for article data for the given
        'article_ids'.
        :param article_ids: List of article ids to retrieve data for.
        :return: Dictionary with article data for each article id."""
        batch_size = self.max_articledata_request
        article_data = {}
        for i in range(0, len(article_ids), batch_size):
            id_batch = ','.join(article_ids[i:i + batch_size])
            r = requests.get(self.api_url + 'article_data',
                             params={'article_id': id_batch},
                             headers={'api-key': self.api_key})

            article_data.update(r.json()['articles'])
        return article_data

    def get_article_feedback(self, user_ids):
        """Queries the arXivDigest API for article feedback for the given
        'user_ids'.
        :param user_ids: List of user ids to retrieve data for.
        :return: Dictionary with article feedback for each user id."""
        batch_size = self.max_userinfo_request
        article_feedback = {}
        for i in range(0, len(user_ids), batch_size):
            id_batch = ','.join([str(u) for u in user_ids[i:i + batch_size]])
            r = requests.get(self.api_url + 'user_feedback/articles',
                             params={'user_id': id_batch},
                             headers={'api-key': self.api_key})
            article_feedback.update(r.json()['user_feedback'])
        return article_feedback

    def send_article_recommendations(self, recommendations):
        """Sends the recommendations to the arXivDigest API.

        :param recommendations: Dictionary of user id to recommendation pairs
        like: user_id:{[ {'article_id': x, score': x, 'explanation': x},..],..}
        :return List of users which recommendations failed for.
        """
        batch_size = self.users_per_recommendation
        failed_users = []
        recommendations = list(recommendations.items())
        for i in range(0, len(recommendations), batch_size):
            recommendation_batch = dict(recommendations[i:i + batch_size])

            r = requests.post(self.api_url + 'recommendations/articles',
                              json={'recommendations': recommendation_batch},
                              headers={'api-key': self.api_key})
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                failed_users.append(recommendation_batch.keys())
                logging.error('Failed recommending batch of users: {}'.format(
                    ', '.join(recommendation_batch.keys())))
                logging.error(r.json())
        return failed_users

    def get_article_recommendations(self, user_ids):
        """Queries the arXivDigest API for article recommendations for the given
        'user_ids'.
        :param user_ids: List of user ids to retrieve data for.
        :return: Dictionary with article recommendations for each user id."""
        batch_size = self.max_userinfo_request
        article_recommendations = {}
        for i in range(0, len(user_ids), batch_size):
            id_batch = ','.join([str(u) for u in user_ids[i:i + batch_size]])
            r = requests.get(self.api_url + 'recommendations/articles',
                             params={'user_id': id_batch},
                             headers={'api-key': self.api_key})
            article_recommendations.update(r.json()['users'])
        return article_recommendations

    def send_topic_recommendations(self, recommendations):
        """Sends the recommendations to the arXivDigest API.
        :param recommendations: Dictionary of user id to recommendation pairs
        like: user_id:[{topic: x, score: x}]
        :return List of users which recommendations failed for.
        """
        batch_size = self.users_per_recommendation
        failed_users = []
        recommendations = list(recommendations.items())
        for i in range(0, len(recommendations), batch_size):
            recommendation_batch = dict(recommendations[i:i + batch_size])
            r = requests.post(self.api_url + 'recommendations/topics',
                              json={'recommendations': recommendation_batch},
                              headers={"api-key": self.api_key})
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError:
                failed_users.append(recommendation_batch.keys())
                logging.error('Failed recommending batch of users: {}'.format(
                    ', '.join(recommendation_batch.keys())))
                logging.error(r.json())
        return failed_users

    def get_topic_feedback(self, user_ids):
        """Queries the arXivDigest API for topic feedback for the given
        'user_ids'.
        :param user_ids: List of user ids to retrieve data for.
        :return: Dictionary with topic feedback for each user id."""
        batch_size = self.max_userinfo_request
        topic_feedback = {}
        for i in range(0, len(user_ids), batch_size):
            id_batch = ','.join([str(u) for u in user_ids[i:i + batch_size]])
            r = requests.get(self.api_url + 'user_feedback/topics',
                             params={'user_id': id_batch},
                             headers={'api-key': self.api_key})
            topic_feedback.update(r.json()['user_feedback'])
        return topic_feedback

    def get_topic_recommendations(self, user_ids):
        """Queries the arXivDigest API for topic recommendations for the given
        'user_ids'.
        :param user_ids: List of user ids to retrieve data for.
        :return: Dictionary with topic recommendations for each user id."""
        batch_size = self.max_userinfo_request
        topic_recommendations = {}
        for i in range(0, len(user_ids), batch_size):
            id_batch = ','.join([str(u) for u in user_ids[i:i + batch_size]])
            r = requests.get(self.api_url + 'recommendations/topics',
                             params={'user_id': id_batch},
                             headers={'api-key': self.api_key})
            topic_recommendations.update(r.json()['users'])
        return topic_recommendations
