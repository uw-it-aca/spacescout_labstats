"""
Tests the k2 endpoint.
"""
from spacescout_labstats.endpoints import k2
import json
import copy
from . import LabstatsTestCase


class K2Test(LabstatsTestCase):
    def test_get_endpoint_data(self):
        """
        This tests the get_endpoint_data method in the k2 endpoint by replacing
        network calls with mocked methods.
        """
        k2_spaces = self.load_json_file('k2_unloaded_spaces.json')

        k2_loaded_spaces = self.load_json_file('k2_loaded_spaces.json')

        setattr(k2.settings, 'K2_URL', 'placeholder_value')

        k2.get_k2_data = self.replacement_get_k2_data()

        k2.get_endpoint_data(k2_spaces)

        self.assertEqual(k2_spaces, k2_loaded_spaces)

    def test_load_k2_data_into_spaces(self):
        """This method tests a good run on the k2_load data. """
        k2_data = self.load_json_file('k2_data.json')
        k2_spaces = self.load_json_file('k2_unloaded_spaces.json')

        k2.load_k2_data_into_spaces(k2_spaces, k2_data["results"]["divs"])

        k2_loaded_spaces = self.load_json_file('k2_loaded_spaces.json')

        self.assertEqual(k2_loaded_spaces, k2_spaces)

    def test_k2_data_entry_validation(self):
        """This method tests the k2 data validation method in k2.py"""
        k2_data = self.load_json_file('k2_data.json')['results']['divs']

        del k2_data[1]['name']
        del k2_data[2]['id']
        del k2_data[3]['count']
        del k2_data[4]['total']

        try:
            k2.validate_k2_data_entry(k2_data[0])
        except Exception as ex:
            self.fail("Good data should not fail validation!")

        with self.assertRaises(Exception):
            k2.validate_k2_data_entry(k2_data[1])

        with self.assertRaises(Exception):
            k2.validate_k2_data_entry(k2_data[2])

        with self.assertRaises(Exception):
            k2.validate_k2_data_entry(k2_data[3])

        with self.assertRaises(Exception):
            k2.validate_k2_data_entry(k2_data[4])

    def test_k2_data_validation(self):
        """Tests the overall k2_data validation"""
        k2_data = self.load_json_file('k2_data.json')

        try:
            k2.validate_k2_data(k2_data)
        except Exception as ex:
            self.fail("Data validation should not fail on good data: %s" % ex)

        k2_missing_results = copy.deepcopy(k2_data)
        del k2_missing_results['results']

        with self.assertRaises(Exception):
            k2.validate_k2_data(k2_missing_results)

        k2_missing_divs = copy.deepcopy(k2_data)
        del k2_missing_divs['results']['divs']

        with self.assertRaises(Exception):
            k2.validate_k2_data(k2_missing_divs)

    def test_k2_validate_space(self):
        """This test tests the space validation for the k2 endpoint."""
        k2_loaded_spaces = self.load_json_file('k2_loaded_spaces.json')

        for space in k2_loaded_spaces:
            try:
                k2.validate_space(space)
            except Exception as ex:
                self.fail("Validation should not vail on good data")

        bad_spaces = copy.deepcopy(k2_loaded_spaces)

        del bad_spaces[0]["extended_info"]["k2_id"]
        del bad_spaces[1]["extended_info"]["k2_name"]

        for space in bad_spaces:
            with self.assertRaises(Exception):
                k2.validate_space(space)

    def replacement_get_k2_data(self):
        """This is a replacement method for getting k2 data """
        k2_data = self.load_json_file('k2_data.json')

        def fake_func():
            return k2_data["results"]["divs"]

        return fake_func
