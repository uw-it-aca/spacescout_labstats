import logging
from django.conf import settings
from spacescout_labstats.utils import clean_spaces_labstats
from SOAPpy import WSDL
import json
import traceback

logger = logging.getLogger(__name__)


def get_spot_search_parameters():
    """
    Returns the URL with which to send a GET request to spotseeker_server and
    retrieve all the spots that need to be updated from seattle_labstats.
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


def get_endpoint_data(labstats_spots):
    """
    Takes in a list of spots from the labstats_daemon and then retrieves their
    labstats information from the seattle labstats service, at which point the
    data is merged and returned.
    """
    try:
        # Updates the num_machines_available extended_info field
        # for spots that have corresponding labstats.
        upload_spots = []

        groups = get_seattle_labstats_data()
        load_labstats_data(labstats_spots, groups)

    except Exception as ex:
        clean_spaces_labstats(labstats_spots)
        logger.error("Error getting labstats stats: %s", str(ex))
        logger.debug(traceback.format_exc())

    return upload_spots


def get_seattle_labstats_data():
    """
    Retrieves the labstats information from the seattle labstats service
    """
    stats = WSDL.Proxy(settings.LABSTATS_URL)
    groups = stats.GetGroupedCurrentStats().GroupStat
    return groups


def load_labstats_data(labstats_spots, groups):
    """
    Applies the data loaded from the labstats webservice to
    """
    for spot in labstats_spots:
        for g in groups:
            # Available data fields froms the labstats
            # groups:
                # g.groupName g.availableCount g.groupId
                # g.inUseCount g.offCount g.percentInUse
                # g.totalCount g.unavailableCount

            if spot['extended_info']['labstats_id'] == g.groupId:

                available = int(g.availableCount)
                total = int(g.totalCount)
                off = int(g.offCount)

                # if (total > 3) and (total - available) < 3:
                #    available = total - 3

                spot['extended_info'].update(
                    auto_labstats_available=available+off,
                    auto_labstats_total=total,
                )

                # why is this here? - Ethan
                spot['location']['longitude'] = \
                    str(spot['location']['longitude'])
                spot['location']['latitude'] = \
                    str(spot['location']['latitude'])

    return labstats_spots
