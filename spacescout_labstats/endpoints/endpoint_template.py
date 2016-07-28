"""
This file contains a template of what an endpoint file should look like.

It also contains more in depth descriptions of the individual methods, what
they should do, and how.


"""


def get_space_search_parameters():
    """
    This method will return the URL to be queried to search for spaces to be
    updated. For example, the online_labstats has the following URL:

    {server}/api/v1/spot/?extended_info:has_online_labstats=true&limit=0

    This tells the server to return all spaces with has_online_labstats= true,
    with no limit.
    """


def get_name():
    """
    This will return the name of this endpoint, primarily for logging
    purposes.
    """
    return "Endpoint Template"


def validate_space(space):
    """
    This method will validate a space, thus ensuring that it is compliant with
    the standards requisite for being updated by the endpoint.

    This method should only be called with spaces already validated by the
    utils.validate_space
    """


def get_endpoint_data(spaces_to_be_updated):
    """
    This is the method that will be called once the spaces have been retrieved
    by a GET to spaceseeker_server with get_space_search_parameters. You should
    then query your endpoint for the data to update these spaces, update the
    spaces(in their original dictionary).
    """


"""
Any other methods are not required and are simply helpder methods
"""
