"""
This file contians tests for cte_techloan.py
"""
from django.conf import settings
from django.test.utils import override_settings
import requests
from mock import patch, Mock
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

    def test_validate_space(self):
        """
        Tests that spaces are validated correctly to ensure that
        a 'cte_techloan_id' is in the extended info of a space
        """
        test_json = self.load_json_file('cte_techloan.json')

        for space in test_json:
            try:
                cte_techloan.validate_space(space)
            except Exception as ex:
                self.fail("Valid data should not fail validation!")

        del test_json[0]['extended_info']['cte_techloan_id']

        with self.assertRaises(Exception):
            cte_techloan.validate_space(test_json[0])

    def test_get_techloan_data(self):
        """
        Tests that getting the data from the techloan instance
        returns the expected data and raises errors appropriately
        """
        test_json = self.load_json_file('cte_techloan_type_data.json')
        status_codes = [200, 400]
        # Mock a get call with different status codes returned
        for status in status_codes:
            mock = Mock()
            mock.status_code = status
            mock.json = Mock(return_value=test_json)

            with patch.object(requests, 'get', return_value=mock):
                techloan_data = cte_techloan.get_techloan_data()
                if (status == 200):
                    self.assertEqual(techloan_data, test_json)
                else:
                    self.assertIs(techloan_data, None)

        # Mock a call with invalid techloan_data
        test_json = 1
        mock = Mock()
        mock.status_code = 200
        mock.json = Mock(return_value=test_json)

        with patch.object(requests, 'get', return_value=mock):
            techloan_data = cte_techloan.get_techloan_data()
            self.assertIs(techloan_data, None)

    def test_get_endpoint_data(self):
        """
        Tests that item availability is retrieved and updated in the spaces
        appropriately
        """
        test_json = self.load_json_file('cte_techloan.json')
        test_json_data = self.load_json_file('cte_techloan_type_data.json')
        # Test getting endpoint data with valid spaces and space data succeeds
        with patch.object(cte_techloan, 'get_techloan_data', return_value=test_json_data):
            cte_techloan.get_endpoint_data(test_json)
        # Test getting endpoint data with invalid data returns None
        with patch.object(cte_techloan, 'get_techloan_data', return_value=None):
            self.assertIs(cte_techloan.get_endpoint_data(test_json), None)

    @override_settings(CTE_TECHLOAN_URL="xxx")
    def test_get_endpoint_data_no_setting(self):
        """
        Tests that an exception is raised when getting endpoint
        data without a CTE_TECHLOAN_URL in settings
        """
        del settings.CTE_TECHLOAN_URL
        with self.assertRaises(Exception):
            cte_techloan.get_endpoint_data(test_json)

    def test_get_techloan_data_by_id(self):
        """
        Tests that the returned techloan_data has a equipment_location_id
        that matches the given id. Also tests that an empty list is
        returned when not found
        """
        # Test with a list of data that have the matching techloan_id
        valid_data = self.load_json_file('cte_techloan_type_data.json')
        returned = cte_techloan.get_techloan_data_by_id(valid_data, 1)
        # Should return a list with data that has the correct id
        self.assertEqual(valid_data, returned)

        # Test with a list with data thats valid but doesnt match the id
        valid_data[0]["equipment_location_id"] = 2
        returned = cte_techloan.get_techloan_data_by_id(valid_data, 1)
        self.assertEqual(returned, [])

    def test_get_space_item_by_type_id(self):
        """
        Tests that the correct space with a cte_type_id that matches the given
        type_id. Also tests that 'None' is returned when not found
        """
        # Test with a list of spaces that have the matching cte_type_id
        valid_spaces = self.load_json_file('cte_techloan.json')
        returned = cte_techloan.get_space_item_by_type_id(1, valid_spaces)
        # Should return a single space with the correct id
        self.assertEqual(valid_spaces[0], returned)

        # Test with a list of spaces that are valid but dont have a matching id
        valid_spaces[0]["extended_info"]["cte_type_id"] = 2
        returned = cte_techloan.get_space_item_by_type_id(1, valid_spaces)
        self.assertIs(returned, None)

        # Test with a list of spaces that do not have a cte_type_id
        invalid_spaces = [{}]
        invalid_spaces[0]["extended_info"] = {}
        returned = cte_techloan.get_space_item_by_type_id(1, invalid_spaces)
        self.assertIs(returned, None)

    def test_validate_techloan_data(self):
        """
        Tests that techloan data is validated appropriately and that
        exceptions are raised with invalid techloan data versions
        """
        valid_type_data = self.load_json_file('cte_techloan_type_data.json')
        # Test validation with data that is of dict type instead of list
        invalid_type_data = {}
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data(invalid_type_data)

        invalid_entry_data = [{}]
        # Test validation with data of correct type containing an invalid entry
        # This should remove the single invalid entry in the invalid entry data
        cte_techloan.validate_techloan_data(invalid_entry_data)
        self.assertEqual(invalid_entry_data, [])

        # Test with data that is of correct type with a valid entry
        cte_techloan.validate_techloan_data(valid_type_data)

    def test_validate_techloan_data_entry(self):
        """
        Tests that a given techloan data entry is validated appropriately
        by testing that each required/necessary field is present in the entry
        """
        data_entry = {}
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["equipment_location_id"] = "UW"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["id"] = 1
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["name"] = "Camera"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["description"] = "Nikon D3200 SLR"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["make"] = "Nikon"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["model"] = "D3200"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["manual_url"] = "http://nikon.com/"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["image_url"] = "http://stlp.uw.edu/nikon.jpg"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["check_out_days"] = 14
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["customer_type_id"] = 1
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["stf_funded"] = True
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["num_active"] = 1
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["_embedded"] = {}
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["_embedded"]["class"] = {}
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["_embedded"]["class"]["name"] = "DSLR Camera"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["_embedded"]["class"]["category"] = "Cameras"
        with self.assertRaises(Exception):
            cte_techloan.validate_techloan_data_entry(data_entry)
        data_entry["_embedded"]["availability"] = [{}]
        data_entry["_embedded"]["availability"][0]["num_available"] = 1
        # data_entry is now valid, should pass validation entirely
        cte_techloan.validate_techloan_data_entry(data_entry)
