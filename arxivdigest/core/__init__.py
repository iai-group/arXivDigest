# -*- coding: utf-8 -*-

import re

from markupsafe import Markup, escape

__author__ = 'Øyvind Jekteberg and Kristian Gingstad'
__copyright__ = 'Copyright 2020, The arXivDigest project'


def md_bold(text):
    """Replaces **text** with bold tags."""
    text = str(escape(text))
    text = re.sub('\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return Markup(text)
