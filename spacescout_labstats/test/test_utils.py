from django.test import TestCase
from spacescout_labstats import utils
from utils_test import get_test_data_directory
import json


class UtilsTest(TestCase):
    """
    Tests the utility methods in utils.py
    """
    def test_uuid_validation(self):
        """
        Tests the UUID validation method is_valid_uuid in labstats_daemon.
        """
        with open(get_test_data_directory() +
                  "uuid_test.json") as test_data_file:
            uuids = json.load(test_data_file)

        for good_uuid in uuids['correct_uuids']:
            is_uuid = utils.is_valid_uuid(good_uuid)
            self.assertTrue(is_uuid, "Failed for good UUID : " + good_uuid)

        for bad_uuid in uuids['malformed_uuids']:
            is_valid_uuid = utils.is_valid_uuid(bad_uuid)
            self.assertEqual(is_valid_uuid, None, "Failed for bad UUID : " +
                             bad_uuid)

    def test_clean_labstats(self):
        """
        This tests the cleaned_labstats_data function in utils.py, ensuring
        that in the event of an error we don't mess up the data through trying
        to delete the outdated labstats info.
        """
        with open(get_test_data_directory() +
                  "seattle_labstats.json") as test_data_file:
            labstats_data = json.load(test_data_file)

        with open(get_test_data_directory() +
                  "seattle_labstats_cleaned.json") as test_data_file:
            cleaned_labstats_data = json.load(test_data_file)

        labstats_data = utils.clean_spaces_labstats(labstats_data)

        self.assertEqual(labstats_data, cleaned_labstats_data)
