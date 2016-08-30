import logging
from django.conf import settings
from spacescout_labstats import utils
from SOAPpy import WSDL
import json
import traceback

logger = logging.getLogger(__name__)


def get_space_search_parameters():
    """
    Returns the URL with which to send a GET request to spaceseeker_server and
    retrieve all the spaces that need to be updated from seattle_labstats.
    """
    url = ("%s/api/v1/spot/?extended_info:has_labstats=true&"
           "center_latitude=%s&center_longitude=%s&distance=%s"
           "&limit=0") \
        % (settings.SS_WEB_SERVER_HOST,
           settings.LS_CENTER_LAT,
           settings.LS_CENTER_LON,
           settings.LS_SEARCH_DISTANCE)
    return url


def get_name():
    """
    Returns the name of the endpoint that this file will hit. For logging.
    """
    return "Seattle Labstats"


def validate_space(space):
    """
    This method will validate a space, thus ensuring that it is compliant with
    the standards requisite for being updated by the seattle labstats endpoint.

    This method should only be called with spaces already validated by the
    utils.validate_space
    """
    if "labstats_id" not in space["extended_info"]:
        raise Exception("labstats_id not present in space #" +
                        str(space['id']))


def get_endpoint_data(labstats_spaces):
    """
    Takes in a list of spaces from the labstats_daemon and then retrieves their
    labstats information from the seattle labstats service, at which point the
    data is merged and returned.
    """
    # Updates the num_machines_available extended_info field
    # for spaces that have corresponding labstats.
    upload_spaces = []

    try:
        groups = get_seattle_labstats_data()
    except SOAPTimeoutError as ex:
        logger.error("SOAPTimeoutError encountered, Seattle labstats"
                     " timed out", exc_info=1)
        return

    # if data retrieval failed, then clean the spaces and log the error
    if groups is None:
        utils.clean_spaces_labstats(labstats_spaces)
        return

    load_labstats_data(labstats_spaces, groups)


def get_seattle_labstats_data():
    """
    Retrieves the labstats information from the seattle labstats service
    """
    try:
        stats = WSDL.Proxy(settings.LABSTATS_URL)
        groups = stats.GetGroupedCurrentStats().GroupStat
    except AttributeError as ex:
        # Temporary fix for debugging AttributeError
        logger.error("AttributeError encountered with " +
                     stats.GetGroupedCurrentStats(), exc_info=1)
        return
    return groups


def load_labstats_data(labstats_spaces, groups):
    """
    Applies the data loaded from the labstats webservice to
    """
    for space in labstats_spaces:
        for g in groups:
            # Available data fields froms the labstats
            # groups:
                # g.groupName g.availableCount g.groupId
                # g.inUseCount g.offCount g.percentInUse
                # g.totalCount g.unavailableCount

            if space['extended_info']['labstats_id'] == g.groupId:

                available = int(g.availableCount)
                total = int(g.totalCount)
                off = int(g.offCount)

                # if (total > 3) and (total - available) < 3:
                #    available = total - 3

                space['extended_info'].update(
                    auto_labstats_available=available+off,
                    auto_labstats_total=total,
                )

                # why is this here? - Ethan
                space['location']['longitude'] = \
                    str(space['location']['longitude'])
                space['location']['latitude'] = \
                    str(space['location']['latitude'])

    return labstats_spaces
