# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='arXivDigest',
    version='1.0',
    packages=find_packages(),
    package_data={'core.mail': ['templates/*.tmpl'],
                  'frontend': ['templates/*.html', 'static/*', 'static/icons/*',
                               'static/javascript/*'
                               ],
                  },
    url='https://github.com/iai-group/arXivDigest',
    author='Øyvind Jekteberg and Kristian Gingstad',
    install_requires=requirements
)
