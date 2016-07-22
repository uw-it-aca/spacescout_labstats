from django.test import TestCase


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
