# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

from arxivdigest.frontend import app

app.js_bundle.build()
app.css_bundle.build()

setup(
    name='arxivdigest',
    version='1.0',
    packages=find_packages(),
    package_data={'arxivdigest.core.mail': ['templates/*.tmpl'],
                  'arxivdigest.frontend': ['templates/*.html',
                                           'static/*',
                                           'static/.webassets-cache/*',
                                           'static/gen/js/*',
                                           'static/gen/css/*',
                                           'static/icons/*',
                                           'static/javascript/*'
                                           ],
                  },
    url='https://github.com/iai-group/arXivDigest',
    author='Øyvind Jekteberg and Kristian Gingstad',
    install_requires=requirements
)
