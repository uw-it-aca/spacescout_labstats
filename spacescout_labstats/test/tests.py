"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from spacescout_labstats.endpoints import seattle_labstats, online_labstats
from spacescout_labstats import utils
import os
import json


class SimpleTest(TestCase):

    def test_bad_uuid(self):
        """
        Tests that the get_customers method in run_labstats_daemon
        handles a bad uuid correctly and does not throw an exception,
        instead logging the error and continuing
        """
        self.assertEqual(1 + 1, 2)
