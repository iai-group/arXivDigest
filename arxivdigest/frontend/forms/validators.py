# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from collections import Counter

from wtforms import ValidationError


class RequireAnyInGroup(object):
    """Validator which only accepts form if at least one field in each group is
    filled out.
    Default null values are,  ['', None]
    """

    def __init__(self, group=1, message=None, null_values=None):
        if not null_values:
            null_values = ['', None]
        self.null_values = null_values
        self.group = group
        self.message = message if message else \
            'You must fill out at least one field in the {} group.'.format(
                group)

    def __call__(self, form, field):
        non_empty_fields_in_group = Counter()
        for field_name in form.data.keys():
            for validator in form[field_name].validators:
                if isinstance(validator, RequireAnyInGroup):
                    field_data = form.data[field_name]
                    if field_data in validator.null_values:
                        continue
                    non_empty_fields_in_group[validator.group] += 1

        for validator in field.validators:
            if isinstance(validator, RequireAnyInGroup):
                if not non_empty_fields_in_group[validator.group]:
                    raise ValidationError(self.message)
