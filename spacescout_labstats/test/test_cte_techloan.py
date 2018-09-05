"""
This file contians tests for cte_techloan.py
"""
from django.conf import settings

from spacescout_labstats.endpoints import cte_techloan
from . import LabstatsTestCase


class CTETechloanTest(LabstatsTestCase):

    def test_hello(self):
        self.assertTrue(True)

    def test_get_space_search_parameters(self):
        """
        Tests that the url constructed for GET requests to spotseeker_server
        is correct and is generated successfully
        """
        server_host = settings.SS_WEB_SERVER_HOST
        expected_url = ("%s/api/v1/spot/?extended_info:app_type=tech&"
                        "extended_info:has_cte_techloan=true&"
                        "limit=0") % (server_host)
        # Assert that the retireved url matches the expected url
        self.assertEquals(expected_url, cte_techloan.get_space_search_parameters())

    def test_get_name(self):
        """
        Tests that the name of the endpoint is correct (logging purposes)
        """
        expected_name = "CTE Tech Loan"
        self.assertEquals(expected_name, cte_techloan.get_name())
