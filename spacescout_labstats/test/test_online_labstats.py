"""
This file contians tests for online_labstats.py
"""
import requests
from mock import patch, Mock

from django.test.utils import override_settings
from django.conf import settings

from spacescout_labstats.endpoints import online_labstats
from . import LabstatsTestCase


class OnlineLabstatsTest(LabstatsTestCase):

    @override_settings(SS_WEB_SERVER_HOST="xxx")
    def test_get_space_search_parameters(self):
        """
        Tests that the url constructed for requests to spotseeker_server
        is correct and generated as expected
        """
        server_host = settings.SS_WEB_SERVER_HOST
        url = "%s/api/v1/spot/?extended_info:has_online_labstats=true&limit=0"\
            % (server_host)
        # Assert that the retrieved url matches the expected url
        self.assertEquals(url, online_labstats.get_space_search_parameters())

    def test_get_name(self):
        """
        Tests that the name of the endpoint is correct (logging purposes)
        """
        expected_name = "Online Labstats"
        self.assertEqual(expected_name, online_labstats.get_name())

    def test_get_endpoint_data(self):
        test_spaces = self.load_json_file('online_labstats_spaces.json')
        # First, get endpoint data with spaces that have appropriate e_i
        with patch.object(online_labstats, 'load_labstats_data') as mock:
            online_labstats.get_endpoint_data(test_spaces)
            mock.assert_called_once()

        # Get endpoint without any labstats data
        self.assertTrue(
            'auto_labstats_total' in test_spaces[0]['extended_info'])
        with patch.object(online_labstats, 'get_online_labstats_data',
                          return_value=None):
            online_labstats.get_endpoint_data(test_spaces)
        # Assert that the space is cleaned, signifying that this case is ran
        self.assertTrue(
            'auto_labstats_total' not in test_spaces[0]['extended_info'])

    def test_get_labstats_customers(self):
        """
        Loads sample JSON data and compares the output of get_customers to the
        format intended.
        """
        # load the content and garbage collect the file object
        test_json = self.load_json_file('bothell_labstats_spaces.json')

        individual_page_dict = {
                                    "UW2 Lower Level Kiosks": 257,
                                    "UW2 First Floor Kiosks": 258,
                                    "UW1 Second Floor Kiosks": 259,
                                    "Open Learning Lab (UW2-140) Mac": 296,
                                    "Open Learning Lab (UW2-140) Pc": 297,
                                    "UW Husky Hall Kiosks": 273,
                                    "UW Husky Village Kiosks": 274,
                                    "UW1 First Floor Kiosks": 250,
                                    "UW2 Second Floor Kiosks": 252,
                                    "UW1 Third Floor Kiosks": 254
                                }

        pages_dict = {1002: individual_page_dict}
        customers_dict = {"749b5ac3-597f-4316-957c-abe939800634": pages_dict}
        customers = online_labstats.get_customers(test_json)
        self.assertEqual(customers, customers_dict)

        # Get customers from spaces that have duplicate labstats lables
        test_spaces = self.load_json_file('online_labstats_spaces.json')
        # Mimic duplicate lables by setting the lables to be the same
        test_label = test_spaces[0]["extended_info"]["labstats_label"]
        test_spaces[1]["extended_info"]["labstats_label"] = test_label

        with patch('spacescout_labstats.endpoints' +
                   '.online_labstats.logger') as mock_log:
            online_labstats.get_customers(test_spaces)
            mock_log.warning.assert_called_once()

    def test_get_online_labstats_data(self):
        test_spaces = self.load_json_file('online_labstats_spaces.json')
        mock = Mock()
        mock.status_code = 200
        mock.json = Mock(return_value=test_spaces)
        customers = online_labstats.get_customers(test_spaces)
        customer = customers['749b5ac3-597f-4316-957c-abe939800634']
        page = customer[1002]
        # test a successful get request & assert the returned spaces match
        with patch.object(requests, 'get', return_value=mock):
            spaces = online_labstats.get_online_labstats_data(customer, page)
            self.assertEqual(test_spaces, spaces)

        with patch.object(requests, 'get', return_value=None) as \
                mock_get, patch('spacescout_labstats.endpoints.' +
                                'online_labstats.logger') as mock_log:
                mock_get.side_effect = Exception()
                ret = online_labstats.get_online_labstats_data(customer, page)
                mock_log.error.assert_called_with('Retrieving labstats' +
                                                  ' page failed!', exc_info=1)
                self.assertIs(ret, None)

        with patch.object(requests, 'get', return_value=None) as \
                mock_get, patch('spacescout_labstats.endpoints.' +
                                'online_labstats.logger') as mock_log:
                mock_get.side_effect = ValueError()
                ret = online_labstats.get_online_labstats_data(customer, page)
                mock_log.error.assert_called_with('Retrieving labstats' +
                                                  ' page failed!', exc_info=1)
                self.assertIs(ret, None)

    def test_get_labstat_by_label(self):
        online_labstats_data = self.load_json_file('online_labstats_data.json')

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "Open Learning Lab "
                                                         "(UW2-140) Mac")

        intended_lab = {
            "Label": "Open Learning Lab (UW2-140) Mac",
            "InUse": 0,
            "Available": 17,
            "Offline": 0,
            "TurnedOn": 17,
            "Total": 17,
            "OrderNum": 1
        }

        self.assertEqual(lab, intended_lab)

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "nfeshufa;elks")

        self.assertIsNone(lab)

    def test_load_labstats_data(self):
        # TODO : test this with bad data somehow
        """
        This tests the utility method that performs the loading of the online
        labstats data into the spaces.
        """
        labstats_spaces = self.load_json_file('bothell_labstats_spaces.json')

        loaded_labstats_spaces = self.load_json_file(
            'loaded_bothell_labstats_spaces.json')

        online_labstats_data = self.load_json_file(
            'online_labstats_data.json')

        customers = online_labstats.get_customers(labstats_spaces)

        customer = customers["749b5ac3-597f-4316-957c-abe939800634"]

        page = customer[1002]

        online_labstats.load_labstats_data(labstats_spaces,
                                           online_labstats_data,
                                           page)

        self.assertEqual(labstats_spaces, loaded_labstats_spaces)

        # Test with bad data
        page = {
            'UW Husky Hall Kiosks': 273
        }
        online_labstats_data["Groups"] = online_labstats_data["Groups"][:1]
        test_spaces = self.load_json_file('online_labstats_spaces.json')[:1]
        with patch('spacescout_labstats.endpoints' +
                   '.online_labstats.logger') as mock_log:
            online_labstats.load_labstats_data(test_spaces,
                                               online_labstats_data,
                                               page)
            mock_log.warning.assert_called_with('space 273 missing' +
                                                ' from spaces!')
            mock_log.reset_mock()

            page = {
                'UW2 Lower Level Kiosks': 257
            }
            online_labstats.load_labstats_data(test_spaces,
                                               online_labstats_data,
                                               page)
            mock_log.warning.assert_called_with('Labstat entry not found for' +
                                                ' label %s and space #257',
                                                u'UW2 Lower Level Kiosks')

    def test_validate_space(self):
        """
        Tests the data validation specific to the online labstats endpoint
        """
        labstats_spaces = self.load_json_file('bothell_labstats_spaces.json')

        for space in labstats_spaces:
            try:
                online_labstats.validate_space(space)
            except Exception as ex:
                self.fail("Good data should not fail validation")

        del labstats_spaces[0]['extended_info']['labstats_customer_id']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[0])

        del labstats_spaces[1]['extended_info']['labstats_label']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[1])

        del labstats_spaces[2]['extended_info']['labstats_page_id']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[2])
