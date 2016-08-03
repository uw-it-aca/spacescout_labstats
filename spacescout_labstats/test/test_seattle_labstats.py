"""
This file contains tests for seattle_labstats.py.
"""
from spacescout_labstats.endpoints import seattle_labstats
from . import LabstatsTestCase


class SeattleLabstatsTest(LabstatsTestCase):

    def test_load_labstats_data(self):
        """
        Tests the loading of the seattle labstats data into the relevant spots
        """
        test_json = self.load_json_file('seattle_labstats.json')

        test_labstats = self.load_seattle_test_data()

        loaded_data = seattle_labstats.load_labstats_data(test_json,
                                                          test_labstats)

        intended_result = self.load_json_file(
            'seattle_labstats_loaded_data.json')

        self.assertEqual(loaded_data, intended_result)

    def test_validate_space(self):

        test_json = self.load_json_file('seattle_labstats.json')

        for space in test_json:
            try:
                seattle_labstats.validate_space(space)
            except Exception as ex:
                self.fail("Valid data should not fail validation!")

        del test_json[0]['extended_info']['labstats_id']

        with self.assertRaises(Exception):
            seattle_labstats.validate_space(test_json[0])

    def load_seattle_test_data(self):
        """
        This method loads the test data that will be used for the seattle
        labstats
        """
        test_json = self.load_json_file('test_seattle_labstats_data.json')

        data_list = [Expando(group) for group in test_json]

        return data_list


class Expando(object):
    def __init__(self, data):
        self.__dict__ = data
