"""
Tests the k2 endpoint.
"""
from django.test import TestCase
from spacescout_labstats.endpoints import k2
from utils_test import get_test_data_directory
import json
import copy


class K2Test(TestCase):
    def test_get_endpoint_data(self):
        """
        This tests the get_endpoint_data method in the k2 endpoint by replacing
        network calls with mocked methods.
        """
        with open(get_test_data_directory() +
                  "k2_unloaded_spaces.json") as test_data_file:
            k2_spaces = json.load(test_data_file)

        with open(get_test_data_directory() +
                  "k2_loaded_spaces.json") as test_data_file:
            k2_loaded_spaces = json.load(test_data_file)

        setattr(k2.settings, "K2_URL", "placeholder_value")

        k2.get_k2_data = replacement_get_k2_data

        k2.get_endpoint_data(k2_spaces)

        self.assertEqual(k2_spaces, k2_loaded_spaces)

    def test_load_k2_data_into_spaces(self):
        """
        This method tests a good run on the k2_load data.
        """
        with open(get_test_data_directory() +
                  "k2_data.json") as test_data_file:
            k2_data = json.load(test_data_file)

        with open(get_test_data_directory() +
                  "k2_unloaded_spaces.json") as test_data_file:
            k2_spaces = json.load(test_data_file)

        k2.load_k2_data_into_spaces(k2_spaces, k2_data["results"]["divs"])

        with open(get_test_data_directory() +
                  "k2_loaded_spaces.json") as test_data_file:
            k2_loaded_spaces = json.load(test_data_file)

        self.assertEqual(k2_loaded_spaces, k2_spaces)

    def test_k2_data_entry_validation(self):
        """
        This method tests the k2 data validation method in k2.py
        """
        with open(get_test_data_directory() +
                  "k2_data.json") as test_data_file:
            k2_data = json.load(test_data_file)

        k2_data = k2_data["results"]["divs"]

        k2_data[1].pop("name", None)
        k2_data[2].pop("id", None)
        k2_data[3].pop("count", None)
        k2_data[4].pop("total", None)

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
        """
        Tests the overall k2_data validation
        """
        with open(get_test_data_directory() +
                  "k2_data.json") as test_data_file:
            k2_data = json.load(test_data_file)

        try:
            k2.validate_k2_data(k2_data)
        except Exception as ex:
            self.fail("Data validation should not fail on good data :" +
                      str(ex))

        k2_missing_results = copy.deepcopy(k2_data)

        k2_missing_results.pop("results", None)

        with self.assertRaises(Exception):
            k2.validate_k2_data(k2_missing_results)

        k2_missing_divs = copy.deepcopy(k2_data)

        k2_missing_divs["results"].pop("divs", None)

        with self.assertRaises(Exception):
            k2.validate_k2_data(k2_missing_divs)

    def test_k2_validate_space(self):
        """
        This test tests the space validation for the k2 endpoint.
        """
        with open(get_test_data_directory() +
                  "k2_loaded_spaces.json") as test_data_file:
            k2_loaded_spaces = json.load(test_data_file)

        for space in k2_loaded_spaces:
            try:
                k2.validate_space(space)
            except Exception as ex:
                self.fail("Validation should not vail on good data")

        bad_spaces = copy.deepcopy(k2_loaded_spaces)

        bad_spaces[0]["extended_info"].pop("k2_id")
        bad_spaces[1]["extended_info"].pop("k2_name")

        for space in bad_spaces:
            with self.assertRaises(Exception):
                k2.validate_space(space)


def replacement_get_k2_data():
    """
    This is a replacement method for getting k2 data
    """
    with open(get_test_data_directory() +
              "k2_data.json") as test_data_file:
        k2_data = json.load(test_data_file)
    return k2_data["results"]["divs"]
