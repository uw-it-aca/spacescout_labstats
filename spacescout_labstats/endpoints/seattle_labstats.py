<<<<<<< HEAD
import logging
from django.conf import settings
from spacescout_labstats.utils import clean_spaces_labstats
from SOAPpy import WSDL
import json

logger = logging.getLogger(__name__)


# TODO : determine if this would be better as an object vs collection of
# static methods
def get_spot_search_parameters():
    url = ("%s/api/v1/spot/?extended_info:has_labstats=true&"
           "center_latitude=%s&center_longitude=%s&distance=%s"
           "&limit=0") \
           % (settings.SS_WEB_SERVER_HOST,
              settings.LS_CENTER_LAT,
              settings.LS_CENTER_LON,
              settings.LS_SEARCH_DISTANCE)
    return url


def get_labstats_data(labstats_spaces):
    try:
        # Updates the num_machines_available extended_info field
        # for spots that have corresponding labstats.
        stats = WSDL.Proxy(settings.LABSTATS_URL)
        groups = stats.GetGroupedCurrentStats().GroupStat
        upload_spaces = []

        for space in labstats_spaces:
            try:
                for g in groups:
                    # Available data fields froms the labstats
                    # groups:
                        # g.groupName g.availableCount g.groupId
                        # g.inUseCount g.offCount g.percentInUse
                        # g.totalCount g.unavailableCount

                    if space['extended_info']['labstats_id'] == \
                            g.groupId:

                        available = int(g.availableCount)
                        total = int(g.totalCount)
                        off = int(g.offCount)
                        if (total > 3)and(total - available) < 3:
                            available = total - 3

                        space['extended_info'].update(
                            auto_labstats_available=available+off,
                            auto_labstats_total=total,
                        )

                        space['location']['longitude'] = \
                            str(space['location']['longitude'])
                        space['location']['latitude'] = \
                            str(space['location']['latitude'])

                        upload_spaces.append({
                            'data': json.dumps(space),
                            'id': space['id'],
                            'etag': space['etag']
                        })

            except Exception as ex:
                print ex
                clean_spaces_labstats(labstats_spaces)
                upload_spaces.append({
                    'data': json.dumps(space),
                    'id': space['id'],
                    'etag': space['etag']
                })
                logger.error("An error occured updating labstats "
                             "spot %s: %s", (space.name, str(ex)))

    except Exception as ex:
        clean_spaces_labstats(labstats_spaces)
        upload_spaces.append({
            'data': json.dumps(space),
            'id': space['id'],
            'etag': space['etag']
        })
        logger.error("Error getting labstats stats: %s", str(ex))

    return upload_spaces


logger = logging.getLogger(__name__)
