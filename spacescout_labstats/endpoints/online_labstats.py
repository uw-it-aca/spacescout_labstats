import logging
from spacescout_labstats.utils import clean_spaces_labstats


logger = logging.getLogger(__name__)


def get_spot_search_parameters(self):
    """
    This is the URL/the parameters that will be used to retrieve spots
    using the cloud based version of labstats.

    has_online_labstats should be true if they are.
    """
    return "%s/api/v1/spot/?extended_info:has_online_labstats=true&limit=0"
