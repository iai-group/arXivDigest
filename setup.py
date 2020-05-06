# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='arxivdigest',
    version='1.0',
    packages=find_packages(),
    package_data={'arxivdigest.core.mail': ['templates/*.tmpl'],
                  'arxivdigest.frontend': ['templates/*.html',
                                           'templates/Macros/*',
                                           'uncompiled_assets/css/*',
                                           'uncompiled_assets/javascript/*',
                                           'static/*',
                                           'static/icons/*',
                                           ],
                  },
    url='https://github.com/iai-group/arXivDigest',
    author='Øyvind Jekteberg and Kristian Gingstad',
    install_requires=requirements
)
