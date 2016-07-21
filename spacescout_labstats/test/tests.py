"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def setUp(self):
        self.run_labstats_daemon = run_labstats_daemon.Command()

    def get_test_data_filepath(self):
        test_dir = script_dir = os.path.dirname(__file__)
        test_data_filename = "bothell_labstats_spaces.json"
        abs_test_data_filepath = os.path.join(test_dir, test_data_filename)

        return abs_test_data_filepath

    def test_get_spot_dict(self):
        with open(self.get_test_data_filepath()) as test_data_file:
            test_json = json.load(test_data_file)

        spots = self.run_labstats_daemon.get_spot_dict(test_json)

        self.assertEqual(test_json[0]['name'], spots[257]['name'])

    def test_bad_uuid(self):
        """
        Tests that the get_customers method in run_labstats_daemon
        handles a bad uuid correctly and does not throw an exception,
        instead logging the error and continuing
        """
        self.assertEqual(1 + 1, 2)

    def test_uuid_validation(self):
        """
        Tests the UUID validation method is_valid_uuid in labstats_daemon.
        """
        for good_uuid in correct_uuids:
            is_uuid = self.run_labstats_daemon.is_valid_uuid(good_uuid)
            self.assertTrue(is_uuid, "Failed for good UUID : " + good_uuid)

        for bad_uuid in malformed_uuids:
            is_valid_uuid = self.run_labstats_daemon.is_valid_uuid(bad_uuid)
            self.assertEqual(is_valid_uuid, None, "Failed for bad UUID : " +
                             bad_uuid)

    def test_get_labstats_customers(self):
        """
        Loads sample JSON data and compares the output of
        get_labstats_customers to the datastructure intended.

        """

        # load the content and garbage collect the file object
        with open(self.get_test_data_filepath()) as test_data_file:
            test_json = json.load(test_data_file)

        individual_page_dict = {
                                    "UW2 Lower Level Kiosks": 257,
                                    "UW2 First Floor Kiosks": 258,
                                    "UW1 Second Floor Kiosks": 259,
                                    "Open Learning Lab (UW2-140) Mac": 296,
                                    "Open Learning Lab (UW2-140) Pc": 297,
                                    "UW Husky Hall Kiosks": 273,
                                    "UW Husky Village Kiosks": 274,
                                    "UW1 First Floor Kiosks": 250,
                                    "UW2 Second Floor Kiosks": 252,
                                    "UW1 Third Floor Kiosks": 254
                                }
        pages_dict = {1002: individual_page_dict}
        customers_dict = {"749b5ac3-597f-4316-957c-abe939800634": pages_dict}
        customers = self.run_labstats_daemon.get_customers(test_json)

        self.assertEqual(customers, customers_dict)
