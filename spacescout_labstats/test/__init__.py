from django.test import TestCase
import json
import os


class LabstatsTestCase(TestCase):

    def load_json_file(self, filename):
        path = os.path.join(self.get_test_data_directory(), filename)
        with open(path) as data_file:
            json_out = json.load(data_file)

        return json_out

    @staticmethod
    def get_test_data_directory():
        """Retrieves the directory in which the test resources are kept. """
        test_dir = os.path.dirname(__file__)
        test_data_filename = "resources/"
        abs_test_data_filepath = os.path.join(test_dir, test_data_filename)

        return abs_test_data_filepath
