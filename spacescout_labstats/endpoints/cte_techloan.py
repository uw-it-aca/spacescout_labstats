"""
This file contains methods which are used to update the online labstats spaces.
"""
import logging
import requests
from django.conf import settings
from spacescout_labstats import utils

logger = logging.getLogger(__name__)


def get_space_search_parameters():
    """
    Returns the URL with which to send a GET request to spaceseeker_server and
    retrieve all the spaces that need to be updated from cte_techloan.
    """
    url = ("%s/api/v1/spot/?extended_info:app_type=tech&"
           "extended_info:has_cte_techloan=true&"
           "limit=0") \
        % (settings.SS_WEB_SERVER_HOST)
    return url


def get_name():
    """
    This will return the name of this endpoint, primarily for logging
    purposes.
    """
    return "CTE Tech Loan"


def validate_space(space):
    """
    This method will validate a space, thus ensuring that it is compliant with
    the standards requisite for being updated by the cte tech loan endpoint.

    This method should only be called with spaces already validated by the
    utils.validate_space
    """
    if "cte_techloan_id" not in space["extended_info"]:
        raise Exception("cte_techloan_id not present in space #" +
                        str(space['id']))


def get_endpoint_data(techloan_spaces):
    """
    will retrieve item availability from the tech loan server and update
    the items in these spaces appropriately
    """
    if not hasattr(settings, 'CTE_TECHLOAN_URL'):
        raise(Exception("Required setting missing: CTE_TECHLOAN_URL"))
    techloan_data = get_techloan_data()

    load_techloan_data_into_spaces(techloan_spaces, techloan_data)


def get_techloan_data():
    """
    Retrieves the data from the techloan instance and returns it.
    """

    techloan_url = settings.CTE_TECHLOAN_URL
    req = requests.get(techloan_url + "api/v1/type/?scope=extended",
                       verify=False)
    techloan_data = req.json()

    try:
        validate_techloan_data(techloan_data)
    except Exception as ex:
        logger.warning(str(ex))
        return None

    return techloan_data


def load_techloan_data_into_spaces(techloan_spaces, techloan_data):
    """
    Loads the techloan data into the techloan_spaces, then returns the list of
    spaces passed.
    """

    for space in techloan_spaces:
        # get the techloan type data by location
        if "cte_techloan_id" not in space["extended_info"]:
            logger.warning("Spot is missing cte_techloan_id! continuing")
            continue

        for item in space["items"]:
            item["extended_info"]["i_is_active"] = False

        tech_types = get_techloan_data_by_id(
            techloan_data, space["extended_info"]["cte_techloan_id"])

        for tech_type in tech_types:
            item = get_space_item_by_type_id(tech_type["id"], space["items"])

            if item is None:
                item = {
                    'name': "%s %s (%d day)" % (tech_type["make"],
                                                tech_type["model"],
                                                tech_type["check_out_days"]),
                    'category': 'Technology Loan',
                    'subcategory': '',
                    'extended_info': {
                        'cte_type_id': tech_type["id"],
                    },
                }
                item["name"] = item["name"][:50]
                space["items"].append(item)

            # update the item
            item["extended_info"]["i_is_active"] = True
            load_techloan_type_to_item(item, tech_type)


def load_techloan_type_to_item(item, tech_type):
    if tech_type["name"]:
        item["name"] = tech_type["name"][:50]
    item["subcategory"] = tech_type["class"]["name"]

    iei = item["extended_info"]
    if tech_type["description"]:
        iei["i_description"] = tech_type["description"][:350]
    iei["i_brand"] = tech_type["make"]
    iei["i_model"] = tech_type["model"]
    if tech_type["manual_url"]:
        iei["i_manual_url"] = tech_type["manual_url"]
    if tech_type["image_url"]:
        iei["i_image_url"] = tech_type["image_url"]
    iei["i_checkout_period"] = tech_type["check_out_days"]
    iei["i_quantity"] = tech_type["num_active"]
    iei["i_available"] = \
        tech_type["availability"][0]["num_available"]

    # Kludge, customer type 4 ("UW Student") is the only type which can (and
    # must) be reserved on-line. Otherwise treated as first-come, first-serve.
    if tech_type["customer_type_id"] == 4:
        iei["i_reservation_required"] = True
    iei["access_limit_role"] = True
    iei["access_role_students"] = True


def get_techloan_data_by_id(techloan_data, techloan_id):
    """
    Goes through a list of techloan data entries and returns the one matching
    techloan_id
    """

    techloan_types = []
    for data in techloan_data:
        if data['equipment_location_id'] == int(techloan_id):
            techloan_types.append(data)

    return techloan_types


def get_space_item_by_type_id(type_id, space_items):
    """
    Goes through a list of items and returns the one matching type_id
    """
    for item in space_items:
        if 'cte_type_id' in item['extended_info'] \
                and item['extended_info']['cte_type_id'] == type_id:
            return item

    return None


def validate_techloan_data(techloan_data):
    """
    Validates data received from the techloan service, in dict form.

    For a sample format, check test/resources/cte_techloan_data.json
    """
    if not isinstance(techloan_data, list):
        raise Exception("Bad data type for techloan_data!")

    # we'll now iterate through the original data points and make sure they're
    # in the right format
    # this list will contain bad data
    to_remove = []

    for data in techloan_data:
        try:
            validate_techloan_data_entry(data)
        except Exception as ex:
            logger.warning("Bad data retrieved from the techloan instance! " +
                           str(data))
            to_remove.append(data)

    for data in to_remove:
        techloan_data.remove(data)


def validate_techloan_data_entry(techloan_data_entry):
    """
    Validates a single techloan data entry, ensuring that all necessary fields
    exist.

    For a sample format, check test/resources/cte_techloan_data.json
    """
    if "equipment_location_id" not in techloan_data_entry:
        raise Exception("Missing location id in techloan data entry!")

    if "id" not in techloan_data_entry:
        raise Exception("Missing id in techloan data entry!")

    if "name" not in techloan_data_entry:
        raise Exception("Missing name in techloan data entry!")

    if "num_active" not in techloan_data_entry:
        raise Exception("Missing num_active in techloan data entry!")

    if "availability" not in techloan_data_entry:
        raise Exception("Missing availability in techloan data entry!")

    if "num_available" not in techloan_data_entry["availability"][0]:
        raise Exception("No \'num_available\' in techloan data entry!")
