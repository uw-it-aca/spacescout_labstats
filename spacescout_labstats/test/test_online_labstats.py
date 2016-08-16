"""
This file contians tests for online_labstats.py
"""
from spacescout_labstats.endpoints import online_labstats
from . import LabstatsTestCase


class OnlineLabstatsTest(LabstatsTestCase):

    def test_get_labstats_customers(self):
        """
        Loads sample JSON data and compares the output of get_customers to the
        format intended.
        """
        # load the content and garbage collect the file object
        test_json = self.load_json_file('bothell_labstats_spaces.json')

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
        customers = online_labstats.get_customers(test_json)

        self.assertEqual(customers, customers_dict)

    def test_get_labstat_by_label(self):
        online_labstats_data = self.load_json_file('online_labstats_data.json')

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "Open Learning Lab "
                                                         "(UW2-140) Mac")

        intended_lab = {
            "Label": "Open Learning Lab (UW2-140) Mac",
            "InUse": 0,
            "Available": 17,
            "Offline": 0,
            "TurnedOn": 17,
            "Total": 17,
            "OrderNum": 1
        }

        self.assertEqual(lab, intended_lab)

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "nfeshufa;elks")

        self.assertIsNone(lab)

    def test_load_labstats_data(self):
        # TODO : test this with bad data somehow
        """
        This tests the utility method that performs the loading of the online
        labstats data into the spaces.
        """
        labstats_spaces = self.load_json_file('bothell_labstats_spaces.json')

        loaded_labstats_spaces = self.load_json_file(
            'loaded_bothell_labstats_spaces.json')

        online_labstats_data = self.load_json_file(
            'online_labstats_data.json')

        customers = online_labstats.get_customers(labstats_spaces)

        customer = customers["749b5ac3-597f-4316-957c-abe939800634"]

        page = customer[1002]

        online_labstats.load_labstats_data(labstats_spaces,
                                           online_labstats_data,
                                           page)

        self.assertEqual(labstats_spaces, loaded_labstats_spaces)

    def test_validate_space(self):
        """
        Tests the data validation specific to the online labstats endpoint
        """
        labstats_spaces = self.load_json_file('bothell_labstats_spaces.json')

        for space in labstats_spaces:
            try:
                online_labstats.validate_space(space)
            except Exception as ex:
                self.fail("Good data should not fail validation")

        del labstats_spaces[0]['extended_info']['labstats_customer_id']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[0])

        del labstats_spaces[1]['extended_info']['labstats_label']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[1])

        del labstats_spaces[2]['extended_info']['labstats_page_id']

        with self.assertRaises(Exception):
            online_labstats.validate_space(labstats_spaces[2])
