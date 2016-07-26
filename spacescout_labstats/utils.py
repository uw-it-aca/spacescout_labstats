from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from django.http import HttpResponse
from django.conf import settings
import oauth2 as oauth
import urllib2
import json
import logging
import time
import os
import re
import sys

logger = logging.getLogger(__name__)


def upload_data(spots):
    """
    Uploads the provided spots to the spotseeker_server instane provided in
    settings.py.

    This function was copy and pasted, for the most part,
    from spacescout_admin utils.py
    """
    # Required settings for the client
    if not hasattr(settings, 'SS_WEB_SERVER_HOST'):
        raise(Exception("Required setting missing: SS_WEB_SERVER_HOST"))

    # create the results log objects
    success_names = []
    failure_descs = []
    warning_descs = []
    puts = []
    posts = []

    # create the OAuth client and consumer used to PUT the data
    consumer = oauth.Consumer(key=settings.SS_WEB_OAUTH_KEY,
                              secret=settings.SS_WEB_OAUTH_SECRET)
    client = oauth.Client(consumer)

    url = "%s/api/v1/spot" % settings.SS_WEB_SERVER_HOST

    for spot in spots:
        # if our spot is malformed, then continue and log the error
        if not validate_spot(spot):
            logger.error("Malformed spot encountered! Attmepting to log id")
            if 'id' in spot.keys():
                logger.error("Malformed spot id : " + str(spot['id']))

            continue

        # prepare the request header and content
        spot_json = json.dumps(spot)
        spot_url = "%s/%s" % (url, spot["id"])

        # should always be PUT since we are only updating spots
        method = 'PUT'

        spot_headers = {"X-OAuth-User": "%s" % "labstats_daemon",
                        "Content-Type": "application/json",
                        "Accept": "application/json"}

        spot_headers['If-Match'] = spot['etag']

        # fire the request
        resp, content = client.request(spot_url,
                                       method,
                                       spot_json,
                                       headers=spot_headers)

        # Responses 200 and 201 mean we've succeeded
        # 200 is OK, 201 is Created
        if resp['status'] != '200' and resp['status'] != '201':
            # if there's another status, log the error

            try:
                error = json.loads(content)
                flocation = error.keys()[0]
                freason = error[flocation]
            except ValueError:
                flocation = resp['status']
                freason = content

            # Add spot attempt to the list of failures
            hold = {
                'fname': spot['name'],
                'flocation': flocation,
                'freason': freason,
            }
            failure_descs.append(hold)
        else:
            # log the success by adding it to the return data
            success_names.append({'name': spot['name'], 'method': method})

            if content:
                url1 = spot_url
            elif resp['location']:
                url1 = '%s/image' % resp['location']
            else:
                hold = {
                    'fname': spot['name'],
                    'flocation': image,
                    'freason': "could not find spot idea; images not posted",
                }
                warning_descs.append(hold)
                break

        if method == 'POST':
            posts.append(spot['name'])
        elif method == 'PUT':
            puts.append(spot['name'])

    # return results
    return {
        'success_names': success_names,
        'failure_descs': failure_descs,
        'warning_descs': warning_descs,
        'posts': posts,
        'puts': puts,
    }


def stop_process(pid, verbose):
    """
    This function stops the process with the given PID. Used to stop existing
    labstats daemons.

    This will remove the file in /tmp/updater/ that belongs to the old process.
    Upon seeing this file deleted, the old process should shut down.
    """
    if verbose:
        logger.info("Stopping process: %s" % pid)
    try:
        # remove the PID file of the other process
        handle = open(_get_tmp_directory() + "%s.stop" % pid, "w")
        handle.close()

        if os.getpgid(int(pid)):
            if verbose:
                logger.info("Waiting")

            # wait for 15 seconds for the other process to die
            for i in range(0, 15):
                if verbose:
                    logger.info(".")
                time.sleep(1)

                try:
                    os.getpgid(int(pid))
                except:
                    # if an exception is thrown, then the process is dead
                    if verbose:
                        logger.info(" Done")
                    return True
            os.remove(_get_tmp_directory() + "%s.stop" % pid)

            # notify admins that the old labstats is still running
            logger.error("The old labstats daemon did not exit!")
            return False
    except OSError:
        # if we get an error and the process doesn't exist, then remove files
        os.remove((_get_tmp_directory() + "/%s.pid" % pid))
        os.remove((_get_tmp_directory() + "/%s.stop" % pid))
        if verbose:
            logger.warning("Old process %s not Found" % pid)
    return True


def clean_spaces_labstats(labstats_spaces):
    """
    Removes all the labstats info from the spaces in case of an error, so that
    we don't give incorrect or outdated info to users.
    """
    for space in labstats_spaces:
        if 'auto_labstats_available' in space['extended_info']:
            del space['extended_info']['auto_labstats_available']
        if 'auto_labstats_total' in space['extended_info']:
            del space['extended_info']['auto_labstats_total']
        if 'auto_labstats_off' in space['extended_info']:
            del space['extended_info']['auto_labstats_off']

    return labstats_spaces


def is_valid_uuid(uuid):
    """
    Checks to see if the string passed is a valid v4 UUID.

    Returns a MatchObject which evaluates to true (but is not equal to) if
    the UUID string is valid, and None if it is not.
    """
    # check the length, as the regex will not catch additional characters
    if len(uuid) is not 36:
        return None

    pattern = re.compile("[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab]"
                         "[0-9a-f]{3}-[0-9a-f]{12}")
    return pattern.match(uuid)


def get_spot_from_spots(spots, spot_id):
    """
    Returns a given spot out of a list of spots, matching by id.
    """
    for spot in spots:
        if spot['id'] == spot_id:
            return spot

    return None


def _get_tmp_directory():
    """
    Returns the directory in which labstats temp files will be stored, and
    creates it if it does not exist
    """
    if not os.path.isdir("/tmp/updater/"):
        os.mkdir("/tmp/updater/", 0700)
    return "/tmp/updater/"


def validate_spot(spot):
    """
    Validates that a given spot has all the fields required to return it to the
    server. Checks id, etag, and name. Accepts both json and a dict.

    Returns True/False
    """
    try:
        if isinstance(spot, basestring):
            spot = json.loads(spot)

    except JSONDecodeError as ex:
        logger.warning("Invalid JSON format.")
        return false

    if not isinstance(spot, dict):
        return False

    # check for keys in the dict
    if ('id' not in spot.keys() or
        'name' not in spot.keys() or
            'etag' not in spot.keys()):
        return False

    # ensure that the fields are the right type
    if (not isinstance(spot['etag'], basestring) or
        not isinstance(spot['id'], int) or
            not isinstance(spot['id'], int)):
        return False

    return True
