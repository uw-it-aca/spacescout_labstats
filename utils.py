from poster.streaminghttp import register_openers
from poster.encode import multipart_encode
from django.http import HttpResponse
from django.conf import settings
import oauth2 as oauth
import urllib2
import json
import time


# This function was copy and pasted, for the most part, from spacescout_admin utils.py
def upload_data(data):
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
        consumer = oauth.Consumer(key=settings.SS_WEB_OAUTH_KEY, secret=settings.SS_WEB_OAUTH_SECRET)
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

        spot_headers = {"XOAUTH_USER": "%s" % "labstats_daemon", "Content-Type": "application/json", "Accept": "application/json"}
        spot_url = url
        method = 'POST'
        #use PUT when spot id is prodived to update the spot
        if spot_id:
            spot_url = "%s/%s" % (url, spot_id)
            method = 'PUT'
            spot_headers['If-Match'] = etag
        resp, content = client.request(spot_url, method, datum, headers=spot_headers)

        #Responses 200 and 201 mean you done good.
        if resp['status'] != '200' and resp['status'] != '201':
            try:
                error = json.loads(content)
                flocation = error.keys()[0]
                freason = error[flocation]
            except ValueError:
                flocation = resp['status']
                freason = content

            #Add spot attempt to the list of failures
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
