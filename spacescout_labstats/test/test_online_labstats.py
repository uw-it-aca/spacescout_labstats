"""
This file contians tests for online_labstats.py
"""
from django.test import TestCase
from spacescout_labstats.endpoints import online_labstats


class LabstatsDaemonTest(TestCase):

    def test_get_labstats_customers(self):
        """
        Loads sample JSON data and compares the output of get_customers to the
        format intended.
        """

        # load the content and garbage collect the file object
        with open(self.get_test_data_directory() +
                  "bothell_labstats_spaces.json") as test_data_file:
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
        customers = online_labstats.get_customers(test_json)

        self.assertEqual(customers, customers_dict)
