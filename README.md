[![Build Status](https://travis-ci.org/uw-it-aca/spacescout_labstats.svg?branch=develop)](https://travis-ci.org/uw-it-aca/spacescout_labstats)  [![Coverage Status](https://coveralls.io/repos/uw-it-aca/spacescout_labstats/badge.svg?branch=master&service=github)](https://coveralls.io/github/uw-it-aca/spacescout_labstats?branch=master)

# Spacescout Labstats

An adaptor for pulling live computer lab data from a LabStats server into spotseeker_server.

Currently, the only thing this app has is a managment command to start and stop a daemon that will update spacescout spots RESTfully with labstats data.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

* Django <1.4.
* A Python installation (2.6 or 2.7)
* pip or easy_install
* git

### Installing

Use pip to install the app as editable from GitHub:

```
pip install -e git+https://github.com/uw-it-aca/spacescout_labstats.git#egg=spacescout_labstats
```
Set the following settings:

*LABSTATS_URL* (string)
The URL of the LabStats server you're making requests to.
Make sure this matches the labstats url you use to get your labstats data.

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

```
LS_CENTER_LAT = '47.655003'
LS_CENTER_LON = '-122.306864'
LS_SEARCH_DISTANCE = '3000'
```

Add spacescout_labstats to your installed apps:

```
INSTALLED_APPS = (
    ...
    'spacescout_labstats',
    ...
)
```
To run the daemon:

```
python manage.py run_labstats_daemon
```

"--run-once" can be added as a flag
"--update-delay <time in minutes>" can be added as a flag (default time is 5 minutes)

To stop the daemon:

```
python manage.py stop_labstats_daemon
```

"--force" can be added as a flag to brutally kill any processes

## Running the tests

```
python manage.py test spacescout_labstats
```

## Deployment

(To be completed)

## Built With

* [Django](http://djangoproject.com/)

## Contributing

Please read [CONTRIBUTING.md] for details on our code of conduct, and the process for submitting pull requests to us. (This has yet to be writtien.)

## Versioning

For the versions available, see the [tags on this repository](https://github.com/uw-it-aca/spacescout_labstats/tags).

## Authors

* [**Academic Experience Design & Delivery**](https://github.com/uw-it-aca)

See also the list of [contributors](https://github.com/uw-it-aca/spotseeker_server/contributors) who participated in this project.

## License

Copyright 2012-2016 UW Information Technology, University of Washington

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
