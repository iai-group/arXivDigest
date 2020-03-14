# -*- coding: utf-8 -*-
__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

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
        if not validEmail(email):
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
        if not validString(firstname, 1, 255):
            raise ValidationError('Invalid firstname format.')
        self._firstname = firstname

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, lastname):
        """Checks if lastname seems valid"""
        if not validString(lastname, 1, 255):
            raise ValidationError('Invalid  lastname fromat.')
        self._lastname = lastname

    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Checks if organization name seems valid"""
        if not validString(organization, 1, 255):
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

        if not validString(dblp_profile, 5, 255):
            raise ValidationError('Invalid DBLP profile.')

        if not dblp_profile.startswith('dblp.org/'):
            raise ValidationError('DBLP profile must start with dblp.org/.')
        self._dblp_profile = dblp_profile

    @property
    def google_scholar_profile(self):
        return self._google_scholar_profile

    @google_scholar_profile.setter
    def google_scholar_profile(self, google_scholar_profile):
        if not google_scholar_profile:
            self._google_scholar_profile = ''
            return

        if not validString(google_scholar_profile, 5, 255):
            raise ValidationError('Invalid Google Scholar profile.')

        if not google_scholar_profile.startswith('scholar.google.com/'):
            raise ValidationError('Google Scholar profile must start with '
                                  'scholar.google.com/.')
        self._google_scholar_profile = google_scholar_profile

    @property
    def semantic_scholar_profile(self):
        return self._semantic_scholar_profile

    @semantic_scholar_profile.setter
    def semantic_scholar_profile(self, semantic_scholar_profile):
        if not semantic_scholar_profile:
            self._semantic_scholar_profile = ''
            return
        if not validString(semantic_scholar_profile, 5, 256):
            raise ValidationError('Invalid Semantic Scholar profile.')

        if not semantic_scholar_profile.startswith(
                'semanticscholar.org/author/'):
            raise ValidationError('Semantic Scholar profile must start with'
                                  ' semanticscholar.org/author/.')
        self._semantic_scholar_profile = semantic_scholar_profile

    @property
    def personal_website(self):
        return self._personal_website

    @personal_website.setter
    def personal_website(self, personal_website):
        if not personal_website:
            self._personal_website = ''
            return

        if not validString(personal_website, 5, 256):
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
    def topics(self, topics, min_topics=3, min_topic_length=3):
        if isinstance(topics, str):
            topics = [topic.strip() for topic in topics.lower().splitlines()
                      if len(topic.strip()) >= min_topic_length]
        else:
            raise ValidationError('Topics must be a newline separated string.')
        if len(topics) < min_topics:
            raise ValidationError('You need to provide at least {} '
                                  'topics.'.format(min_topics))

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
