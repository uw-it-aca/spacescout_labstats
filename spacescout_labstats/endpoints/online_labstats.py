"""
This file contains methods which are used to update the online labstats spots.
"""
import logging
from spacescout_labstats import utils
import requests
import json
import urllib3
from django.conf import settings

# we need to disable warnings because requests does not like our outdated
# packages.
requests.packages.urllib3.disable_warnings()


logger = logging.getLogger(__name__)


def get_spot_search_parameters():
    """
    This is the URL/the parameters that will be used to retrieve spots
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


def get_endpoint_data(labstats_spaces):
    """
    Retrieves the data relevant to the spaces passed to this method and then
    loads it into the spaces provided, which are then returned.
    """
    customers = get_customers(labstats_spaces)

    for customer in customers:
        for page in customers[customer]:
            response = get_online_labstats_data(customer, page)

            page = customers[customer][page]

            load_labstats_data(labstats_spaces, response, page)

    return labstats_spaces


def get_customers(spot_json):
        """
        Takes in the JSON from querying spotseeker_server and formats it.

        # TODO : rewrite data description
        The data is organized in a dict, in which the customer_id(UUID string)
        is the first key, and then individual pages are listed, matching labels
        to spot ids
        """
        customers = {}

        for spot in spot_json:
            # TODO : handle missing and malformed fields
            # TODO : create json validation method?
            if 'labstats_customer_id' not in spot['extended_info']:
                logger.error("Customer ID missing in an online labstats spot")
                continue

            customer_id = spot['extended_info']['labstats_customer_id']

            # TODO : determine a way to have a reasonable amount of output
            # and not be emailing the admins every 15 minutes
            # ensure that customer_id is a UUID and raise an error if not
            if not utils.is_valid_uuid(customer_id):
                logger.error("Customer UUID " + customer_id + " is not valid"
                             " for spot #" + spot['id'])
                continue

            # if customer_id is not in customers then create a dict
            if customer_id not in customers:
                customers[customer_id] = dict()
            page_id = int(spot['extended_info']['labstats_page_id'])

            # if page_id is not in customers then create a dict
            if page_id not in customers[customer_id]:
                customers[customer_id][page_id] = {}

            spot_label = spot['extended_info']["labstats_label"]

            # make sure that there is only one spot with that label
            if spot_label in customers[customer_id][page_id]:
                other_id = customers[customer_id][page_id][spot_label]
                logger.error("There appear to be multiple spots with the"
                             "label \'" + spot_label+"\',spot #" + spot['id'] +
                             " and " + str(other_id))
                continue

            customers[customer_id][page_id][spot_label] = spot['id']

        return customers


def get_online_labstats_data(customer, page):
    """
    Hits the endpoint for online.labstats.com to retrieve the information
    with which we'll update the spots.

    customer is an UUID, page is an int
    """
    try:
        url = "http://online.labstats.com/api/public/GetPublicApiData/"

        response = requests.get(url + str(page),
                                headers={"Authorization": customer},
                                verify=False)

        spots = response.json()
    except Exception as ex:
        logger.warning("Retrieving labstats page failed! Exception is"
                       " %s", ex)
        return None
    except ValueError as ex:
        logger.warning("Invalid json received from online labstats service!"
                       "Body is " + response.content)
        return None

    return spots


def load_labstats_data(spots, labstats_data, page_dict):
    """
    Loads the data retrieved from the online labstats service into the spaces.
    """
    # create the list of spaces to be uploaded
    upload_spaces = []

    for page_id, spot_id in page_dict.iteritems():
        # get the spot by it's id in page_dict
        spot = utils.get_spot_from_spots(spots, spot_id)

        if spot is None:
            logger.warning("Spot " + spot_id + " missing from spots!")

        # retrieve the labstat info for this spot
        spot_labstat = get_labstat_entry_by_label(labstats_data,
                                                  spot["extended_info"]
                                                  ["labstats_label"])

        if spot_labstat is None:
            logger.warning("Labstat entry not found for label %s and spot id" +
                           spot['id'], spot["extended_info"]["labstats_label"])
            continue

        # load the dict into a variable for easy access
        extended_info = spot["extended_info"]

        # load the new labstats info into the spot's extended_info
        extended_info["auto_labstats_available"] = spot_labstat["Available"]

        extended_info["auto_labstats_available"] += spot_labstat["Offline"]

        extended_info["auto_labstats_total"] = spot_labstat["Total"]

    return spots


def get_labstat_entry_by_label(labstats_data, label):
    """
    Takes in data retreived from the labstat service and loops through it,
    searching for a given label.
    """
    for labstat in labstats_data["Groups"]:
        if(labstat["Label"] == label):
            return labstat

    return None
