from spacescout_labstats import utils
from . import LabstatsTestCase


class UtilsTest(LabstatsTestCase):
    """Tests the utility methods in utils.py"""
    def test_uuid_validation(self):
        """
        Tests the UUID validation method is_valid_uuid in labstats_daemon.
        """
        uuids = self.load_json_file('uuid_test.json')

        for good_uuid in uuids['correct_uuids']:
            is_uuid = utils.is_valid_uuid(good_uuid)
            self.assertTrue(is_uuid, "Failed for good UUID: %s" % good_uuid)

        for bad_uuid in uuids['malformed_uuids']:
            is_valid_uuid = utils.is_valid_uuid(bad_uuid)
            self.assertIsNone(is_valid_uuid, "Failed for bad UUID: %s" %
                              bad_uuid)

    def test_clean_labstats(self):
        """
        This tests the cleaned_labstats_data function in utils.py, ensuring
        that in the event of an error we don't mess up the data through trying
        to delete the outdated labstats info.
        """
        labstats_data = self.load_json_file('seattle_labstats.json')
        cleaned_data = self.load_json_file('seattle_labstats_cleaned.json')

        labstats_data = utils.clean_spaces_labstats(labstats_data)

        self.assertEqual(labstats_data, cleaned_data)

    def validate_space(self):
        """
        This validates a space, ensuring that universal fields (id and etag)
        haven't been corrupted.
        """
        test_json = self.load_json_file('bothell_labstats_spaces.json')
        # test the validation against good data
        for space in test_json:
            self.assertTrue(utils.validate_space(space))

        # invalidate some spaces and ensure that they fail
        del test_json[0]['id']
        self.assertFalse(utils.validate_space(test_json[0]))

        del test_json[1]['etag']
        self.assertFalse(utils.validate_space(test_json[1]))

        del test_json[2]['name']
        self.assertFalse(utils.validate_space(test_json[2]))

        test_json[3]['id'] = str(test_json[3]['id'])
        self.assertFalse(utils.validate_space(test_json[3]))
