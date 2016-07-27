"""
This is the endpoint for updating the computer usage from the k2 server
"""
from spacescout_labstats import utils
from django.conf import settings
import json
import requests
import logging

requests.packages.urllib3.disable_warnings()

logger = logging.getLogger(__name__)


def get_space_search_parameters():
    """
    This method will return the URL to be queried to search for spaces to be
    updated. For example, the online_labstats has the following URL:

    {server}/api/v1/spot/?extended_info:has_k2=true&limit=0

    This tells the server to return all spaces with has_online_labstats= true,
    with no limit.
    """
    url = ("%s/api/v1/spot/?extended_info:has_k2=true&limit=0" %
           settings.SS_WEB_SERVER_HOST)
    return url


def get_name():
    """
    This will return the name of this endpoint, primarily for logging
    purposes.
    """
    return "K2"


def validate_space(space):
    """
    This method will validate a space, thus ensuring that it is compliant with
    the standards requisite for being updated by the k2 endpoint.

    This method should only be called with spaces already validated by the
    utils.validate_space
    """
    if 'k2_id' not in space['extended_info'] and \
            'k2_name' not in space['extended_info']:
        raise Exception("Missing K2 identifier for space " + str(space['id']))


def get_endpoint_data(k2_spaces):
    """
    This method retrieves the data from the K2 server and then loads it into
    the spaces, returning them to be updated
    """
    if not hasattr(settings, 'K2_URL'):
        raise(ImproperlyConfigured("Required setting missing: "
                                   "K2_URL"))
    k2_data = get_k2_data()

    # if the k2 server is not working, then clean the spaces and return
    if k2_data is None:
        utils.clean_spaces_labstats(k2_spaces)
        logger.errror("K2 data retrieval failed!")
        return

    load_k2_data_into_spaces(k2_spaces, k2_data)


def get_k2_data():
    """
    Retrieves the data from the k2 instance and returns it.
    """

    k2_url = settings.K2_URL
    req = requests.get()
    k2_data = req.json()

    try:
        validate_k2_data(k2_data)
    except Exception as ex:
        logger.warning(str(ex))
        return None

    k2_data = k2_data["results"]["divs"]

    return k2_data


def load_k2_data_into_spaces(k2_spaces, k2_data):
    """
    Loads the k2 data into the k2_spaces, then returns the list of spaces
    passed.
    """

    for space in k2_spaces:

        # get the k2 data by id if applicable, name if not
        if "k2_id" in space["extended_info"]:
            data = get_k2_data_by_id(k2_data, space["extended_info"]["k2_id"])
        elif "k2_name" in space["extended_info"]:
            data = get_k2_data_by_name(k2_data, space["extended_info"]
                                       ["k2_name"])

        if data is None:
            logger.warning("Data not found as referenced by spot! Cleaning and"
                           " continuing")
            utils.clean_spaces_labstats(data)
            continue

        # get the total and available number of computers
        total = data["total"]
        available = total - data["count"]

        # update the spot
        space["extended_info"]["auto_labstats_total"] = total
        space["extended_info"]["auto_labstats_available"] = available


def get_k2_data_by_id(k2_data, k2_id):
    """
    Goes through a list of k2 data entries and returns the one matching k2_id
    """
    for data in k2_data:
        if data['id'] == k2_id:
            return data

    return None


def get_k2_data_by_name(k2_data, k2_name):
    """
    Goes through a list of k2 data entries and returns the one matching k2_name
    """
    for data in k2_data:
        if data['name'] == k2_name:
            return data

    return None


def validate_k2_data(k2_data):
    """
    Validates data received from the k2 service, in dict form.

    For a sample format, check test/resources/k2_data.json
    """
    if not isinstance(k2_data, dict):
        raise Exception("Bad data type for k2_data!")

    if "results" not in k2_data:
        raise Exception("No \'Results\' field in the k2_data!")

    if "divs" not in k2_data["results"]:
        raise Exception("No \'divs\' field in the k2_data!")

    # we'll now iterate through the original data points and make sure they're
    # in the right format
    # this list will contain bad data
    to_remove = []

    for data in k2_data["results"]["divs"]:
        try:
            validate_k2_data_entry(data)
        except Exception as ex:
            logger.warning("Bad data retrieved from the k2 instance! " +
                           str(data))
            to_remove.append(data)

    for data in to_remove:
        k2_data.remove(data)


def validate_k2_data_entry(k2_data_entry):
    """
    Validates a single k2 data entry, ensuring that all necessary fields exist.

    For a sample format, check test/resources/k2_data.json
    """
    if "id" not in k2_data_entry:
        raise Exception("Missing id in k2 data entry!")

    if "name" not in k2_data_entry:
        raise Exception("Missing name in k2 data entry!")

    if "total" not in k2_data_entry:
        raise Exception("Missing total in k2 data entry!")

    if "count" not in k2_data_entry:
        raise Exception("Missing count in k2 data entry!")
