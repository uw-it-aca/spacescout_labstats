

logger = logging.getLogger(__name__)


class SeattleLabstats():

    def get_spot_search_parameters():
        """
        This is the URL/the parameters that will be used to retrieve spots.
        """
        return "%s/api/v1/spot/?extended_info:has_online_labstats=true&limit=0"
