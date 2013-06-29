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
