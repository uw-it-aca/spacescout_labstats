"""
This file contains methods which are used to update the online labstats spaces.
"""
import logging
from spacescout_labstats import utils
import requests
import json
import urllib3
from django.conf import settings

requests.packages.urllib3.disable_warnings()


logger = logging.getLogger(__name__)


def get_space_search_parameters():
    """
    This is the URL/the parameters that will be used to retrieve spaces
    using the cloud based version of labstats.

    has_online_labstats should be true if they are.
    """
    url = "%s/api/v1/spot/?extended_info:has_online_labstats=true&limit=0"\
          % (settings.SS_WEB_SERVER_HOST)

    return url


def get_name():
    """
    Returns the name of the endpoint that this file will hit. For logging.
    """
    return "Online Labstats"


def validate_space(space):
    """
    This method will validate a space, thus ensuring that it is compliant with
    the standards requisite for being updated by the online labstatsd endpoint.

    This method should only be called with spaces already validated by the
    utils.validate_space
    """
    if "labstats_customer_id" not in space["extended_info"]:
        raise Exception("Missing labstats_customer_id for space " + str)

    if "labstats_page_id" not in space["extended_info"]:
        raise Exception("Missing labstats_page_id for space " + str)

    if "labstats_label" not in space["extended_info"]:
        raise Exception("Missing labstats_label for space " + str)


def get_endpoint_data(labstats_spaces):
    """
    Retrieves the data relevant to the spaces passed to this method and then
    loads it into the spaces provided, which are then returned.
    """
    customers = get_customers(labstats_spaces)

    for customer in customers:
        for page in customers[customer]:
            response = get_online_labstats_data(customer, page)

            if response is None:
                raise Exception("Online labstats data retrieval failed!")

            page = customers[customer][page]

            load_labstats_data(labstats_spaces, response, page)


def get_customers(spaces):
        """
        Takes in the JSON from querying spaceseeker_server and formats it.

        The data is organized in a dict, in which the customer_id(UUID string)
        is the first key, and then individual pages are listed, matching labels
        to space ids

        {
        "749b5ac3-597f-4316-957c-abe939800634" : {
            1002 : ["Label" : 248]
            }
        }
        """
        customers = {}
        to_delete = []

        for space in spaces:
            if 'labstats_customer_id' not in space['extended_info']:
                logger.error("Customer ID missing in an online labstats space")
                to_delete.append(space)
                continue

            customer_id = space['extended_info']['labstats_customer_id']

            # ensure that customer_id is a UUID and raise an error if not
            if not utils.is_valid_uuid(customer_id):
                logger.error("Customer UUID " + customer_id + " is not valid"
                             " for space #" + space['id'])
                to_delete.append(space)
                continue

            # if customer_id is not in customers then create a dict
            if customer_id not in customers:
                customers[customer_id] = dict()
            page_id = int(space['extended_info']['labstats_page_id'])

            # if page_id is not in customers then create a dict
            if page_id not in customers[customer_id]:
                customers[customer_id][page_id] = {}

            space_label = space['extended_info']["labstats_label"]

            # make sure that there is only one space with that label
            if space_label in customers[customer_id][page_id]:
                other_id = customers[customer_id][page_id][space_label]
                logger.error("There appear to be multiple spaces with the"
                             "label \'" + space_label+"\',space #" +
                             space['id'] + " and " + str(other_id))
                continue

            customers[customer_id][page_id][space_label] = space['id']

        # remove all spaces that had an error and should not be updated
        for space in to_delete:
            spaces.remove(space)

        return customers


def get_online_labstats_data(customer, page):
    """
    Hits the endpoint for online.labstats.com to retrieve the information
    with which we'll update the spaces.

    customer is an UUID, page is an int
    """
    try:
        url = "http://online.labstats.com/api/public/GetPublicApiData/"

        response = requests.get(url + str(page),
                                headers={"Authorization": customer},
                                verify=False)

        spaces = response.json()
    except Exception as ex:
        logger.error("Retrieving labstats page failed! Exception is"
                     " %s", ex)
        return None
    except ValueError as ex:
        logger.error("Invalid json received from online labstats service!"
                     "Body is " + response.content)
        return None

    return spaces


def load_labstats_data(spaces, labstats_data, page_dict):
    """
    Loads the data retrieved from the online labstats service into the spaces.
    """
    # create the list of spaces to be uploaded
    upload_spaces = []
    to_delete = []

    for page_id, space_id in page_dict.iteritems():
        # get the space by it's id in page_dict
        space = utils.get_space_from_spaces(spaces, space_id)

        if space is None:
            logger.warning("space " + space_id + " missing from spaces!")
            continue

        # retrieve the labstat info for this space
        space_labstat = get_labstat_entry_by_label(labstats_data,
                                                   space["extended_info"]
                                                   ["labstats_label"])

        if space_labstat is None:
            logger.warning("Labstat entry not found for label %s and space #" +
                           space['id'], space["extended_info"]
                           ["labstats_label"])
            to_delete.append(space)
            continue

        # load the dict into a variable for easy access
        extended_info = space["extended_info"]

        # load the new labstats info into the space's extended_info
        extended_info["auto_labstats_available"] = space_labstat["Available"]

        extended_info["auto_labstats_available"] += space_labstat["Offline"]

        extended_info["auto_labstats_total"] = space_labstat["Total"]

    # remove all spaces that had an error and should not be updated
    for space in to_delete:
        spaces.remove(space)


def get_labstat_entry_by_label(labstats_data, label):
    """
    Takes in data retreived from the labstat service and loops through it,
    searching for a given label.
    """
    for labstat in labstats_data["Groups"]:
        if(labstat["Label"] == label):
            return labstat

    return None
