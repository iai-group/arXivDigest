# -*- coding: utf-8 -*-

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'

from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import RadioField
from wtforms import SelectField
from wtforms import TextAreaField
from wtforms.validators import AnyOf
from wtforms.validators import DataRequired
from wtforms.validators import Length

from arxivdigest.frontend.forms.validators import RequireAnyInGroup


class FeedbackForm(FlaskForm):
    """Form used by users to give feedback on the service."""

    feedback_type = SelectField('Feedback type',
                                choices=[('Bug', 'Found a bug'),
                                         ('Feature', 'Feature request'),
                                         ('Other', 'Other')],
                                validators=[DataRequired()]
                                )

    feedback_text = TextAreaField('Feedback:',
                                  validators=[
                                      RequireAnyInGroup(group='feedback'),
                                      Length(max=2500)
                                  ],
                                  render_kw={'maxlength': '2500'})


class ArticleFeedbackForm(FeedbackForm):
    """Form used by users to give feedback on articles."""

    feedback_type = HiddenField('Feedback type', default='Recommendation',
                                validators=[DataRequired(),
                                            AnyOf(['Recommendation'])]
                                )
    relevance = RadioField(
        'How relevant is this recommendation to you?',
        validators=[
            RequireAnyInGroup(group='feedback'),
        ],
        coerce=lambda i: None if i in [None, 'None'] else int(i),
        choices=[(None, 'No opinion'), (0, 'Not relevant at all'),
                 (1, 'Somewhat'), (2, 'Highly')
                 ],
        default=None
    )

    expl_satisfaction = RadioField(
        'This explanation is useful.',
        validators=[
            RequireAnyInGroup(group='feedback'),
        ],
        coerce=lambda i: None if i in [None, 'None'] else int(i),
        choices=[(None, 'No opinion'), (0, 'Not at all'),
                 (1, 'Somewhat'), (2, 'Very much')
                 ],
        default=None
    )

    expl_persuasiveness = RadioField(
        'This explanation sounds convincing.',
        validators=[
            RequireAnyInGroup(group='feedback'),
        ],
        coerce=lambda i: None if i in [None, 'None'] else int(i),
        choices=[(None, 'No opinion'), (0, 'Not at all'),
                 (1, 'Somewhat'), (2, 'Very much')
                 ],
        default=None
    )

    expl_transparency = RadioField(
        'This explanation helps me understand the reasoning behind this recommendation.',
        validators=[
            RequireAnyInGroup(group='feedback'),
        ],
        coerce=lambda i: None if i in [None, 'None'] else int(i),
        choices=[(None, 'No opinion'), (0, 'Not at all'),
                 (1, 'Somewhat'), (2, 'Very much')
                 ],
        default=None
    )

    expl_scrutability = RadioField(
        'This explanation allows me to tell the system if it misunderstood my preferences.',
        validators=[
            RequireAnyInGroup(group='feedback'),
        ],
        coerce=lambda i: None if i in [None, 'None'] else int(i),
        choices=[(None, 'No opinion'), (0, 'Not at all'),
                 (1, 'Somewhat'), (2, 'Very much')
                 ],
        default=None
    )
