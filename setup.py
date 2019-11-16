# Copyright (c) 2019, DjaoDjin inc.
# All rights reserved.

from distutils.core import setup

import envconnect

requirements = []
with open('./requirements.txt') as requirements_txt:
    for line in requirements_txt:
        prerequisite = line.split('#')[0].strip()
        if prerequisite:
            requirements += [prerequisite]

setup(
    name='envconnect',
    version=envconnect.__version__,
    author='DjaoDjin inc.',
    author_email='support@djaodjin.com',
    install_requires=requirements,
    packages=[
        'envconnect',
        'envconnect.templatetags',
        'envconnect.management',
        'envconnect.management.commands',
        'envconnect.urls',
        'envconnect.urls.api',
        'envconnect.urls.views',
        'envconnect.api',
        'envconnect.views'
    ],
    url='https://github.com/djaodjin/envconnect.git',
    description='Web application for assessment against best practices',
    long_description=open('README.md').read(),
)
