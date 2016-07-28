"""
This file contains tests for seattle_labstats.py.
"""
from django.test import TestCase
from test_utils import get_test_data_directory
from spacescout_labstats.endpoints import seattle_labstats
import json


class SeattleLabstatsTest(TestCase):
    def test_load_labstats_data(self):
        """
        Tests the loading of the seattle labstats data into the relevant spots
        """
        with open(get_test_data_directory() +
                  "seattle_labstats.json") as test_data_file:
            test_json = json.load(test_data_file)

        test_labstats = load_seattle_test_data()
        loaded_data = seattle_labstats.load_labstats_data(test_json,
                                                          test_labstats)

        with open(get_test_data_directory() +
                  "seattle_labstats_loaded_data.json") as test_data_file:
            intended_result = json.load(test_data_file)

        self.assertEqual(loaded_data, intended_result)

    def test_validate_space(self):
        with open(get_test_data_directory() +
                  "seattle_labstats.json") as test_data_file:
            test_json = json.load(test_data_file)

        for space in test_json:
            try:
                seattle_labstats.validate_space(space)
            except Exception as ex:
                self.fail("Valid data should not fail validation!")

        test_json[0]['extended_info'].pop("labstats_id", None)

        with self.assertRaises(Exception):
            seattle_labstats.validate_space(test_json[0])


class Expando(object):
    pass


def load_seattle_test_data():
    """
    This method loads the test data that will be used for the seattle labstats
    """
    with open(get_test_data_directory() +
              "test_seattle_labstats_data.json") as test_data_file:
        test_json = json.load(test_data_file)

    data_list = []

    attributes = ['groupName', 'availableCount', 'groupId', 'inUseCount',
                  'offCount', 'percentInUse', 'totalCount', 'unavailableCount']

    for group in test_json:
        obj = Expando()
        for attr in attributes:
            setattr(obj, attr, group[attr])

        data_list.append(obj)

    return data_list
