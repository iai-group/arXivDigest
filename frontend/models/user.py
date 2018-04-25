__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

import jwt
import datetime
import re
import datetime
from frontend.models.errors import ValidationError


class User():
    '''User class containing most user attributes'''

    def __init__(self, user):
        self.email = user.get('email')
        self.password = user.get('password')
        self.firstName = user.get('firstName')
        self.lastName = user.get('lastName')
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
        if re.match('^[a-zA-Z0-9.!#$%&’*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$', email) is None:
            raise ValidationError('Invalid value:%s' % email, 'invalid email')
        self._email = email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        if not self.validPassword(password):
            raise ValidationError('Invalid value:Password', 'invalid password')
        self._password = password

    @property
    def firstName(self):
        return self._firstName

    @firstName.setter
    def firstName(self, firstName):
        '''Checks if firstname seems valid'''
        # ^([\p{L}'\-\.]+ )+[\p{L}'\-\.]+$|^[\p{L}'\-\.]+$ unsuported with regular python regex
        if type(firstName) is not str or not len(firstName) > 0 or len(firstName) > 60:
            raise ValidationError('Invalid value:%s' %
                                  firstName, 'invalid firstname')
        self._firstName = firstName

    @property
    def lastName(self):
        return self._lastName

    @lastName.setter
    def lastName(self, lastName):
        '''Checks if lastname seems valid'''
        if type(lastName) is not str or not len(lastName) > 0 or len(lastName) > 60:
            raise ValidationError('Invalid value:%s' %
                                  lastName, 'invalid lastname')
        self._lastName = lastName

    @property
    def webpages(self):
        return self._webpages

    @webpages.setter
    def webpages(self, webpages):
        webpages = [
            page for page in webpages if page is not '' and page is not None]
        if len(webpages) < 1:
            raise ValidationError(
                'You must provide atleast one webpage', 'invalid webpage')
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
        elif digestfrequency == '3 days':
            digestfrequency = 3
        if digestfrequency not in [1, 3, 7]:
            raise ValidationError(
                'Invalid value:Digest Frequency', 'invalid digest frequency')
        self._digestfrequency = digestfrequency

    @staticmethod
    def validPassword(password):
        '''Checks if password is complicated enough'''
        if re.match('(?=^.{9,256}$)(?=.*\d)(?=.*\W+)(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$', password) is None:
            return False
        return True
