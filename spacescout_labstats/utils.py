from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from django.http import HttpResponse
from django.conf import settings
import oauth2 as oauth
import urllib2
import json
import time
import os
import re
import sys


def upload_data(data):
    """
    Uploads the provided spots to the spotseeker_server instane provided in
    settings.py.

    This function was copy and pasted, for the most part,
    from spacescout_admin utils.py
    """
    # Required settings for the client
    if not hasattr(settings, 'SS_WEB_SERVER_HOST'):
        raise(Exception("Required setting missing: SS_WEB_SERVER_HOST"))

    success_names = []
    failure_descs = []
    warning_descs = []
    puts = []
    posts = []

    for datum in data:
        try:
            spot_id = datum["id"]
        except:
            spot_id = None
        try:
            etag = datum["etag"]
            if not etag:
                etag = "There was an error!"
        except:
            etag = None
        datum = datum["data"]

        info = json.loads(datum)
        consumer = oauth.Consumer(key=settings.SS_WEB_OAUTH_KEY,
                                  secret=settings.SS_WEB_OAUTH_SECRET)
        try:
            images = info['images']
        except:
            images = []

        if 'name' in info.keys():
            spot_name = info['name']
        else:
            spot_name = 'NO NAME'

        client = oauth.Client(consumer)
        url = "%s/api/v1/spot" % settings.SS_WEB_SERVER_HOST

        spot_headers = {"X-OAuth-User": "%s" % "labstats_daemon",
                        "Content-Type": "application/json",
                        "Accept": "application/json"}
        spot_url = url
        method = 'POST'
        # use PUT when spot id is prodived to update the spot
        if spot_id:
            spot_url = "%s/%s" % (url, spot_id)
            method = 'PUT'
            spot_headers['If-Match'] = etag
        resp, content = client.request(spot_url,
                                       method,
                                       datum,
                                       headers=spot_headers)

        # Responses 200 and 201 mean you done good.
        if resp['status'] != '200' and resp['status'] != '201':
            try:
                error = json.loads(content)
                flocation = error.keys()[0]
                freason = error[flocation]
            except ValueError:
                flocation = resp['status']
                freason = content

            # Add spot attempt to the list of failures
            hold = {
                'fname': spot_name,
                'flocation': flocation,
                'freason': freason,
            }
            failure_descs.append(hold)
        else:
            success_names.append({'name': spot_name, 'method': method})

            if content:
                url1 = spot_url
            elif resp['location']:
                url1 = '%s/image' % resp['location']
            else:
                hold = {
                    'fname': spot_name,
                    'flocation': image,
                    'freason': "could not find spot idea; images not posted",
                }
                warning_descs.append(hold)
                break

        if method == 'POST':
            posts.append(spot_name)
        elif method == 'PUT':
            puts.append(spot_name)

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
    """
    if verbose:
        print "Stopping process: %s" % pid
    try:
        handle = open(_get_tmp_directory() + "%s.stop" % pid, "w")
        handle.close()
        if os.getpgid(int(pid)):
            if verbose:
                sys.stdout.write("Waiting")
            sys.stdout.flush()
            for i in range(0, 15):
                if verbose:
                    sys.stdout.write(".")
                sys.stdout.flush()
                time.sleep(1)
                try:
                    os.getpgid(int(pid))
                except:
                    if verbose:
                        print " Done"
                    return True
            os.remove(_get_tmp_directory() + "%s.stop" % pid)
            if verbose:
                print " Process did not end"
            return False
    except OSError:
        os.remove((_get_tmp_directory() + "/%s.pid" % pid))
        os.remove((_get_tmp_directory() + "/%s.stop" % pid))
        if verbose:
            print "Old process %s not Found" % pid
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
