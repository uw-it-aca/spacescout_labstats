

logger = logging.getLogger(__name__)


# TODO : determine if this would be better as an object vs collection of
# static methods
class OnlineLabstats():

    def get_spot_search_parameters():
        return "%s/api/v1/spot/?extended_info:has_labstats=true&"
        "center_latitude=%s&center_longitude=%s&distance=%s"
        "&limit=0"

    def get_labstats_data(labstats_spaces):
        try:
            # Updates the num_machines_available extended_info field
            # for spots that have corresponding labstats.
            stats = WSDL.Proxy(settings.LABSTATS_URL)
            groups = stats.GetGroupedCurrentStats().GroupStat

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
                    if space['extended_info'][
                        'auto_labstats_available'] or \
                            space['extended_info'][
                                'auto_labstats_available'] == 0:
                        del space['extended_info'][
                            'auto_labstats_available']
                    if space['extended_info'][
                        'auto_labstats_total'] or \
                            space['extended_info'][
                                'auto_labstats_total'] == 0:
                        del space['extended_info'][
                            'auto_labstats_total']
                    if space['extended_info'][
                        'auto_labstats_off'] or \
                            space['extended_info'][
                                'auto_labstats_off'] == 0:
                        del space['extended_info']['auto_labstats_off']

                    upload_spaces.append({
                        'data': json.dumps(space),
                        'id': space['id'],
                        'etag': space['etag']
                    })

                    logger.error("An error occured updating labstats "
                                 "spot %s: %s", (space.name, str(ex)))

        except Exception as ex:
            for space in labstats_spaces:
                if space['extended_info'][
                    'auto_labstats_available'] or \
                        space['extended_info'][
                            'auto_labstats_available'] == 0:
                    del space['extended_info'][
                        'auto_labstats_available']
                if space['extended_info'][
                    'auto_labstats_total'] or \
                        space['extended_info'][
                            'auto_labstats_total'] == 0:
                    del space['extended_info']['auto_labstats_total']
                if space['extended_info'][
                    'auto_labstats_off'] or \
                        space['extended_info'][
                            'auto_labstats_off'] == 0:
                    del space['extended_info']['auto_labstats_off']

                upload_spaces.append({
                    'data': json.dumps(space),
                    'id': space['id'],
                    'etag': space['etag']
                })

            logger.error("Error getting labstats stats: %s", str(ex))

    return upload_spaces
