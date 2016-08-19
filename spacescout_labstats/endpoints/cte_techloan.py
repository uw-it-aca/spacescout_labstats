"""
This file contains methods which are used to update the online labstats spaces.
"""
import logging
from django.conf import settings

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
    This is the method that will be called once the spaces have been retrieved
    by a GET to spaceseeker_server with get_space_search_parameters. You should
    then query your endpoint for the data to update these spaces, update the
    spaces(in their original dictionary).

    will retrieve item availability from the cte tech loan server and update
    the items in these spaces appropriately
    """


"""
Any other methods are not required and are simply helpder methods
"""
