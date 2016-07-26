"""
This file contians tests for online_labstats.py
"""
from django.test import TestCase
from spacescout_labstats.endpoints import online_labstats
from utils_test import get_test_data_directory
import json


class OnlineLabstatsTest(TestCase):

    def test_get_labstats_customers(self):
        """
        Loads sample JSON data and compares the output of get_customers to the
        format intended.
        """
        # load the content and garbage collect the file object
        with open(get_test_data_directory() +
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

    def test_get_labstat_by_label(self):
        with open(get_test_data_directory() +
                  "online_labstats_data.json") as test_data_file:
            online_labstats_data = json.load(test_data_file)

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "Open Learning Lab "
                                                         "(UW2-140) Mac")

        intended_lab = """{
          \"Label\": \"Open Learning Lab (UW2-140) Mac\",
          "InUse": 0,
          "Available": 17,
          "Offline": 0,
          "TurnedOn": 17,
          "Total": 17,
          "OrderNum": 1
        }"""

        intended_lab = json.loads(intended_lab)

        self.assertEqual(lab, intended_lab)

        lab = online_labstats.get_labstat_entry_by_label(online_labstats_data,
                                                         "nfeshufa;elks")

        self.assertTrue(lab is None)

    def test_load_labstats_data(self):
        # TODO : test this with bad data somehow
        """
        This tests the utility method that performs the loading of the online
        labstats data into the spaces.
        """
        with open(get_test_data_directory() +
                  "bothell_labstats_spaces.json") as test_data_file:
            labstats_spaces = json.load(test_data_file)

        with open(get_test_data_directory() +
                  "loaded_bothell_labstats_spaces.json") as test_data_file:
            loaded_labstats_spaces = json.load(test_data_file)

        with open(get_test_data_directory() +
                  "online_labstats_data.json") as test_data_file:
            online_labstats_data = json.load(test_data_file)

        customers = online_labstats.get_customers(labstats_spaces)

        customer = customers["749b5ac3-597f-4316-957c-abe939800634"]

        page = customer[1002]

        response = online_labstats.load_labstats_data(labstats_spaces,
                                                      online_labstats_data,
                                                      page)

        self.assertEqual(response, loaded_labstats_spaces)

    def get_labstat_entry_by_label(self):
        """
        Tests the method to get a labstats entry by it's label.
        """
        with open(get_test_data_directory() +
                  "online_labstats_data.json") as test_data_file:
            online_labstats_data = json.load(test_data_file)

        for labstat in online_labstats_data['Groups']:

            returned_labstat = get_labstat_entry_by_label(labstat["Label"])
            self.assertEqual(returned_labstat, labstat)

        self.assertEqual(None, get_labstat_entry_by_label("swfjaeijs"))
