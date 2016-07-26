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

    def validate_spot(self):
        """
        This validates a spot, ensuring that universal fields (id and etag)
        haven't been corrupted.
        """
        with open(get_test_data_directory() +
                  "bothell_labstats_spaces.json") as test_data_file:
            test_json = json.load(test_data_file)

        # test the validation against good data
        for spot in test_json:
            self.assertTrue(utils.validate_spot(spot))

        # invalidate some spots and ensure that they fail
        test_json[0].pop('id')
        self.assertFalse(utils.validate_spot(test_json[0]))

        test_json[1].pop('etag')
        self.assertFalse(utils.validate_spot(test_json[1]))

        test_json[2].pop('name')
        self.assertFalse(utils.validate_spot(test_json[2]))

        test_json[3]['id'] = str(test_json[0]['id'])
        self.assertFalse(utils.validate_spot(test_json[3]))
