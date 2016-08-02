#!/usr/bin/env python

from distutils.core import setup

setup(name='SpaceScout-Labstats',
      version='1.0',
      description='Labstats bridge for SpaceScout',
      install_requires=[
                        'Django>=1.4,<1.5',
                        'oauth2<=1.5.211',
                        'simplejson>=2.1',
                        'soappy',
                        'poster',
                        'requests',
                        'urllib3',
                       ],
      )
