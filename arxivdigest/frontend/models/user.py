# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

import re

from arxivdigest.core.config import CONSTANTS
from arxivdigest.frontend.models.errors import ValidationError
from arxivdigest.frontend.models.validate import validEmail
from arxivdigest.frontend.models.validate import validPassword
from arxivdigest.frontend.models.validate import validString


class User():
    """User class containing most user attributes"""

    def __init__(self, user, require_password=True):
        self.require_password = require_password
        self.email = user.get('email')
        self.password = user.get('password')
        self.firstname = user.get('firstname')
        self.lastname = user.get('lastname')
        self.organization = user.get('organization')
        self.dblp_profile = user.get('dblp_profile', '')
        self.google_scholar_profile = user.get('google_scholar_profile', '')
        self.semantic_scholar_profile = user.get('semantic_scholar_profile', '')
        self.personal_website = user.get('personal_website', '')
        self.topics = user.get('topics')
        self.categories = user.get('categories')
        self.notification_interval = user.get('notification_interval')

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        """Checks if email is valid email format"""
        if len(email) > CONSTANTS.max_email_length or not validEmail(email):
            raise ValidationError('Invalid email.')
        self._email = email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if self.require_password and not validPassword(password):
            raise ValidationError('Invalid password format.')
        self._password = password

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, firstname):
        """Checks if firstname seems valid"""
        if not validString(firstname, 1, CONSTANTS.max_human_name_length):
            raise ValidationError('Invalid firstname format.')
        self._firstname = firstname

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, lastname):
        """Checks if lastname seems valid"""
        if not validString(lastname, 1, CONSTANTS.max_human_name_length):
            raise ValidationError('Invalid  lastname fromat.')
        self._lastname = lastname

    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Checks if organization name seems valid"""
        if not validString(organization, 1, CONSTANTS.max_organization_length):
            raise ValidationError('Invalid organization name format.')
        self._organization = organization

    @property
    def dblp_profile(self):
        return self._dblp_profile

    @dblp_profile.setter
    def dblp_profile(self, dblp_profile):
        if not dblp_profile:
            self._dblp_profile = ''
            return

        min_length = CONSTANTS.min_url_length
        max_length = CONSTANTS.max_url_length
        if not validString(dblp_profile, min_length, max_length):
            raise ValidationError('Invalid DBLP profile.')

        allowed_prefixes = ('https://dblp.org/', 'https://dblp.uni-trier.de/', 
            'dblp.uni-trier.de/', 'dblp.org/')
        if not dblp_profile.startswith(allowed_prefixes):
            raise ValidationError('DBLP url prefix does not match DBLP links.')

        dblp_profile = dblp_profile.replace('dblp.uni-trier.de', 'dblp.org')
        self._dblp_profile = dblp_profile

    @property
    def google_scholar_profile(self):
        return self._google_scholar_profile

    @google_scholar_profile.setter
    def google_scholar_profile(self, google_scholar_profile):
        if not google_scholar_profile:
            self._google_scholar_profile = ''
            return

        min_length = CONSTANTS.min_url_length
        max_length = CONSTANTS.max_url_length
        if not validString(google_scholar_profile, min_length, max_length):
            raise ValidationError('Invalid Google Scholar profile.')

        allowed_prefixes = ('scholar.google.com/', 'https://scholar.google.com/')
        if not google_scholar_profile.startswith(allowed_prefixes):
            raise ValidationError('Google Scholar url prefix does not match Google Scholar links.')
        self._google_scholar_profile = google_scholar_profile

    @property
    def semantic_scholar_profile(self):
        return self._semantic_scholar_profile

    @semantic_scholar_profile.setter
    def semantic_scholar_profile(self, semantic_scholar_profile):
        if not semantic_scholar_profile:
            self._semantic_scholar_profile = ''
            return

        min_length = CONSTANTS.min_url_length
        max_length = CONSTANTS.max_url_length
        if not validString(semantic_scholar_profile, min_length, max_length):
            raise ValidationError('Invalid Semantic Scholar profile.')

        allowed_prefixes = ('semanticscholar.org/author/',
                            'https://www.semanticscholar.org/author/',
                            'www.semanticscholar.org/author/',
                            'https://semanticscholar.org/author/')
        if not semantic_scholar_profile.startswith(allowed_prefixes):
            raise ValidationError('Semantic Scholar url prefix does not match Semantic Scholar links.')

        semantic_scholar_profile = semantic_scholar_profile.replace('www.','')
        self._semantic_scholar_profile = semantic_scholar_profile

    @property
    def personal_website(self):
        return self._personal_website

    @personal_website.setter
    def personal_website(self, personal_website):
        if not personal_website:
            self._personal_website = ''
            return
        min_length = CONSTANTS.min_url_length
        max_length = CONSTANTS.max_url_length
        if not validString(personal_website, min_length, max_length):
            raise ValidationError('Invalid personal website.')
        self._personal_website = personal_website

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, categories):
        if isinstance(categories, str):
            categories = [x for x in categories.splitlines() if x is not '']
        self._categories = categories

    @property
    def topics(self):
        return self._topics

    @topics.setter
    def topics(self, topics):
        min_topics = CONSTANTS.min_topics_per_user
        max_length = CONSTANTS.max_topic_length

        if isinstance(topics, str):
            topics = [topic.strip() for topic in topics.lower().splitlines()]
        else:
            raise ValidationError('Topics must be a newline separated string.')
        if len(topics) < min_topics:
            raise ValidationError('You need to provide at least {} '
                                  'topics.'.format(min_topics))

        for topic in topics:
            if not validString(topic, 1, max_length):
                raise ValidationError(
                    'Topics must be shorter than {}.'.format(max_length))
            if not re.match('^[0-9a-zA-Z\- ]+$',topic):
                raise ValidationError('Topics must not contain special characters.')

        self._topics = topics

    @property
    def notification_interval(self):
        return self._notification_interval

    @notification_interval.setter
    def notification_interval(self, notification_interval):
        """Sets value of notification_interval"""
        if notification_interval == '7':
            notification_interval = 7
        elif notification_interval == '1':
            notification_interval = 1
        if notification_interval not in [1, 7]:
            raise ValidationError('Invalid value:Digest Frequency')
        self._notification_interval = notification_interval
