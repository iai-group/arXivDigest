# -*- coding: utf-8 -*-
__author__ = "Øyvind Jekteberg and Kristian Gingstad"
__copyright__ = "Copyright 2018, The ArXivDigest Project"

from arXivDigest.frontend.models.errors import ValidationError
from arXivDigest.frontend.models.validate import validEmail
from arXivDigest.frontend.models.validate import validString


class System():
    '''User class containing most user attributes'''

    def __init__(self, system):
        self.email = system.get('email')
        self.contact = system.get('contact')
        self.name = system.get('name')
        self.organization = system.get('organization')

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
    def contact(self):
        return self._contact

    @contact.setter
    def contact(self, contact):
        '''Checks if contact seems valid'''
        if not validString(contact, 1, 255):
            raise ValidationError('Invalid contact name.')
        self._contact = contact

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        '''Checks if name seems valid'''
        if not validString(name, 1, 255):
            raise ValidationError('Invalid system name.')
        self._name = name

    @property
    def organization(self):
        return self._organization

    @organization.setter
    def organization(self, organization):
        '''Checks if organization seems valid'''
        if not validString(organization, 1, 255):
            raise ValidationError('Invalid organization name')
        self._organization = organization
