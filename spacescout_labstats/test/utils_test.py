"""
A file containing utilities used by the test suite for spacescout_labstats.
"""
import os


def get_test_data_directory():
    """
    Retrieves the directory in which the test resources are kept
    """
    test_dir = script_dir = os.path.dirname(__file__)
    test_data_filename = "resources/"
    abs_test_data_filepath = os.path.join(test_dir, test_data_filename)

    return abs_test_data_filepath
