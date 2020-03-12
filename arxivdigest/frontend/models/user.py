# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

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
        self.first_name = user.get('first_name')
        self.last_name = user.get('last_name')
        self.organization = user.get('organization')
        self.dblp_profile = user.get('dblp', '')
        self.google_scholar_profile = user.get('google_scholar', '')
        self.semantic_scholar_profile = user.get('semantic_scholar', '')
        self.personal_website = user.get('personal_website', '')
        self.topics = user.get('topics')
        self.categories = user.get('categories')
        self.digestfrequency = user.get('digest_frequency')

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
    def first_name(self):
        return self._first_name

    @first_name.setter
    def first_name(self, first_name):
        """Checks if firstname seems valid"""
        if not validString(first_name, 1, 255):
            raise ValidationError('Invalid firstname format.')
        self._first_name = first_name

    @property
    def last_name(self):
        return self._last_name

    @last_name.setter
    def last_name(self, last_name):
        """Checks if lastname seems valid"""
        if not validString(last_name, 1, 255):
            raise ValidationError('Invalid  lastname fromat.')
        self._last_name = last_name

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
            categories = [x for x in categories.split(',') if x is not '']
        self._categories = categories

    @property
    def topics(self):
        return self._topics

    @topics.setter
    def topics(self, topics, min_topics=3, min_topic_length=3):
        if isinstance(topics, str):
            topics = topics.lower().replace('\n', ' ').replace('\r', '')
            topics = [topic.strip() for topic in topics.split(',')
                      if len(topic.strip()) >= min_topic_length]
        else:
            raise ValidationError('Topics must be a comma separated string.')
        if len(topics) < min_topics:
            raise ValidationError('User must have at least {} '
                                  'topics.'.format(min_topics))

        self._topics = topics

    @property
    def digestfrequency(self):
        return self._digestfrequency

    @digestfrequency.setter
    def digestfrequency(self, digestfrequency):
        """Sets value of digestfrequency"""
        if digestfrequency == '7 days':
            digestfrequency = 7
        elif digestfrequency == '1 day':
            digestfrequency = 1
        if digestfrequency not in [1, 7]:
            raise ValidationError('Invalid value:Digest Frequency')
        self._digestfrequency = digestfrequency
