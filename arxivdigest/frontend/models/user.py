# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from arxivdigest.frontend.models.errors import ValidationError
from arxivdigest.frontend.models.validate import validEmail
from arxivdigest.frontend.models.validate import validPassword
from arxivdigest.frontend.models.validate import validString


class User():
    '''User class containing most user attributes'''

    def __init__(self, user):
        self.email = user.get('email')
        self.password = user.get('password')
        self.firstName = user.get('firstName')
        self.lastName = user.get('lastName')
        self.organization = user.get('organization')
        self.webpages = user.get('website', [])
        self.keywords = user.get('keywords')
        self.categories = user.get('categories')
        self.digestfrequency = user.get('digestFrequency')

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, email):
        '''Checks if email is valid email format'''
        if not validEmail(email):
            raise ValidationError('Invalid email.')
        self._email = email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if not validPassword(password):
            raise ValidationError('Invalid password format.')
        self._password = password

    @property
    def firstName(self):
        return self._firstName

    @firstName.setter
    def firstName(self, firstName):
        '''Checks if firstname seems valid'''
        if not validString(firstName, 1, 255):
            raise ValidationError('Invalid firstname format.')
        self._firstName = firstName

    @property
    def lastName(self):
        return self._lastName

    @lastName.setter
    def lastName(self, lastName):
        '''Checks if lastname seems valid'''
        if not validString(lastName, 1, 255):
            raise ValidationError('Invalid  lastname fromat.')
        self._lastName = lastName

    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self,organization):
        """Checks if organization name seems valid"""
        if not validString(organization, 1, 255):
            raise ValidationError('Invalid organization name format.')
        self._organization = organization

    @property
    def webpages(self):
        return self._webpages

    @webpages.setter
    def webpages(self, webpages):
        webpages = [
            page for page in webpages if page is not '' and page is not None]
        if len(webpages) < 1:
            raise ValidationError('You must provide at least one webpage')
        self._webpages = webpages

    @property
    def categories(self):
        return self._categories

    @categories.setter
    def categories(self, categories):
        if isinstance(categories, str):
            categories = [x for x in categories.split(',') if x is not '']
        self._categories = categories

    @property
    def digestfrequency(self):
        return self._digestfrequency

    @digestfrequency.setter
    def digestfrequency(self, digestfrequency):
        '''Sets value of digestfrequency'''
        if digestfrequency == '7 days':
            digestfrequency = 7
        elif digestfrequency == '1 day':
            digestfrequency = 1
        if digestfrequency not in [1, 7]:
            raise ValidationError('Invalid value:Digest Frequency')
        self._digestfrequency = digestfrequency
