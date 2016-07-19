spacescout_labstats
===================

An adaptor for pulling live computer lab data from a LabStats server into spotseeker_server.

Currently, the only thing this app has is a managment command to start and stop a daemon that will update spacescout spots RESTfully with labstats data.
The daemon can be started with:
* run_labstats_daemon
"--run-once" can be added as a flag
"--update-delay <time in minutes>" can be added as a flag (default time is 5 minutes)

and can be stopped with:
* stop_labstats_daemon
"--force" can be added as a flag to brutally kill any processes

Also, make sure the LABSTATS_URL variable in your settings.py matches the labstats url you use to get your labstats data.

# Configuration

## Required settings

*LABSTATS_URL* (string)
The URL of the LabStats server you're making requests to.

*SS_WEB_SERVER_HOST* (string)
The URL of the spotseeker_server you're PUTting updates to.

*SS_WEB_OAUTH_KEY* (string)
A key from a trusted OAuth consumer generated on the spotseeker_server.

*SS_WEB_OAUTH_SECRET* (string)
A secret from the trusted OAuth consumer generated on the spotseeker_server.

*LS_CENTER_LAT* (string)
Latitude for a center point to begin the search for Spaced to update from.

*LS_CENTER_LON* (string)
Longitude for a center point to begin the search for Spaced to update from.

*LS_SEARCH_DISTANCEi* (string)
The distance from the center point in meters to search.

Some sample settings:
LS_CENTER_LAT = '47.655003'
LS_CENTER_LON = '-122.306864'
LS_SEARCH_DISTANCE = '3000'

You will also need to ensure that "labstats_daemon" is added to your spotseeker_server's SPOTSEEKER_AUTH_ADMINS
