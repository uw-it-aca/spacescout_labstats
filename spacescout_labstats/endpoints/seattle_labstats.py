import logging
from django.conf import settings
from spacescout_labstats.utils import clean_spaces_labstats
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


def get_endpoint_data(labstats_spaces):
    """
    Takes in a list of spaces from the labstats_daemon and then retrieves their
    labstats information from the seattle labstats service, at which point the
    data is merged and returned.
    """
    # Updates the num_machines_available extended_info field
    # for spaces that have corresponding labstats.
    upload_spaces = []

    groups = get_seattle_labstats_data()

    if groups is None:
        raise Exception("Data not retrieved from " + get_name() + " endpoint!")

    load_labstats_data(labstats_spaces, groups)

    return upload_spaces


def get_seattle_labstats_data():
    """
    Retrieves the labstats information from the seattle labstats service
    """
    stats = WSDL.Proxy(settings.LABSTATS_URL)
    groups = stats.GetGroupedCurrentStats().GroupStat
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

            if "labstats_id" not in space['extended_info']:
                logger.warning("No labstats_id in space " + space['name'] +
                               str(space['id']))
                clean_spaces_labstats([space])

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
