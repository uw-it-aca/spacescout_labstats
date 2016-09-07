#!/usr/bin/env python

from distutils.core import setup

setup(name='SpaceScout-Labstats',
      version='1.0',
      description='Labstats bridge for SpaceScout',
      install_requires=[
                        'Django>=1.4,<1.5',
                        'oauth2<=1.5.211',
                        'simplejson>=2.1',
			# wstools 0.4.4 has a bug that we need to avoid
                        'wstools<=0.4.3',
                        'soappy',
                        'poster',
                        'requests',
                        'urllib3',
                        'mock',
                        'PermissionsLogging',
                       ],
      )
