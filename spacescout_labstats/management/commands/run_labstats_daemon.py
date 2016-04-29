"""
This provides a managament command to run a daemon that will frequently update
the spots that have corresponding labstats information with the number of
machines available and similar information.
"""
from django.core.management.base import BaseCommand
from spacescout_labstats.utils import upload_data
from django.conf import settings
from optparse import make_option
from SOAPpy import WSDL
import os
import sys
import time
import re
import atexit
import oauth2
import json
import logging
import stop_process

#TODO: how should the log location be set?
#logging.basicConfig(filename='/tmp/labstats_updater.log', level=logging.DEBUG, filemode='w')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'This updates spots with labstats data'

    option_list = BaseCommand.option_list + (
        make_option('--daemonize',
                    dest='daemon',
                    default=True,
                    action='store_true',
                    help='This will set the updater to run as a daemon.'),
        make_option('--update-delay',
                    dest='update_delay',
                    type='int',
                    default=5,
                    help='The number of minutes between update attempts.'),
        make_option('--run-once',
                    dest='run_once',
                    default=False,
                    action='store_true',
                    help='This will allow the updater to run just once.'),
        make_option('--verbose',
                    dest='verbose',
                    default=False,
                    action='store_true',
                    help='print out detailed log in console'),
    )

    def handle(self, *args, **options):
        """
        This is the entry point for the management command. It will handle
        daemonizing the script as needed.
        """

        """
        Everytime if a user tries to run a new process while an old process is
        running. The old process will be terminated before the new process could
        start.
        """
        if (self.process_exists()):
            try:
                files = os.listdir("/tmp/updater")
            except OSError:
                sys.exit(0)
            for filename in files:
                matches = re.match(r"^([0-9]+).pid$", filename)
                if matches:
                    pid = matches.group(1)
                    verbose = options["verbose"]
                    stop_process.stop_process(pid, verbose)

        atexit.register(self.remove_pid_file)

        daemon = options["daemon"]

        if daemon:
            logger.info("starting the updater as a daemon")
            pid = os.fork()
            if pid == 0:
                os.setsid()

                pid = os.fork()
                if pid != 0:
                    os._exit(0)

            else:
                os._exit(0)

            self.create_pid_file()
            try:
                self.controller(options["update_delay"], options["run_once"])
            except Exception as ex:
                logger.error("Error running the controller: %s", str(ex))

        else:
            logger.info("starting the updater as an interactive process")
            self.create_pid_file()
            self.controller(options["update_delay"], options["run_once"])

    def controller(self, update_delay, run_once=False):
        """
        This is responsible for the workflow of orchestrating
        the updater process.
        """
        if not hasattr(settings, 'SS_WEB_SERVER_HOST'):
            raise(Exception("Required setting missing: SS_WEB_SERVER_HOST"))
        consumer = oauth2.Consumer(key=settings.SS_WEB_OAUTH_KEY, secret=settings.SS_WEB_OAUTH_SECRET)
        client = oauth2.Client(consumer)

        while True:
            if self.should_stop():
                sys.exit()

            # This allows for a one time run via interactive process for automated testing
            if run_once:
                self.create_stop_file()

            upload_spaces = []

            if not hasattr(settings, 'LS_CENTER_LAT'):
                raise(Exception("Required setting missing: LS_CENTER_LAT"))
            if not hasattr(settings, 'LS_CENTER_LON'):
                raise(Exception("Required setting missing: LS_CENTER_LON"))
            if not hasattr(settings, 'LS_SEARCH_DISTANCE'):
                raise(Exception("Required setting missing: LS_SEARCH_DISTANCE"))
            try:
                url = "%s/api/v1/spot/?extended_info:has_labstats=true&center_latitude=%s&center_longitude=%s&distance=%s&limit=0" % (settings.SS_WEB_SERVER_HOST, settings.LS_CENTER_LAT, settings.LS_CENTER_LON, settings.LS_SEARCH_DISTANCE)
                resp, content = client.request(url, 'GET')
                labstats_spaces = json.loads(content)

                try:
                    # Updates the num_machines_available extended_info field for spots that have corresponding labstats.
                    stats = WSDL.Proxy(settings.LABSTATS_URL)
                    groups = stats.GetGroupedCurrentStats().GroupStat

                    for space in labstats_spaces:
                        try:
                            for g in groups:
                                # Available data fields froms the labstats groups:
                                    # g.groupName g.availableCount g.groupId g.inUseCount g.offCount g.percentInUse g.totalCount g.unavailableCount

                                if space['extended_info']['labstats_id'] == g.groupId:

                                    available = int(g.availableCount)
                                    total = int(g.totalCount)
                                    off = int(g.offCount)
                                    if (total > 3) and ((total - available) < 3):
                                        available = total - 3

                                    space['extended_info'].update(
                                        auto_labstats_available = available + off,
                                        auto_labstats_total = total,
                                    )

                                    space['location']['longitude'] = str(space['location']['longitude'])
                                    space['location']['latitude'] = str(space['location']['latitude'])

                                    upload_spaces.append({
                                        'data': json.dumps(space),
                                        'id': space['id'],
                                        'etag': space['etag']
                                    })

                        except Exception as ex:
                            if space['extended_info']['auto_labstats_available'] or space['extended_info']['auto_labstats_available'] == 0:
                                del space['extended_info']['auto_labstats_available']
                            if space['extended_info']['auto_labstats_total'] or space['extended_info']['auto_labstats_total'] == 0:
                                del space['extended_info']['auto_labstats_total']
                            if space['extended_info']['auto_labstats_off'] or space['extended_info']['auto_labstats_off'] == 0:
                                del space['extended_info']['auto_labstats_off']

                            upload_spaces.append({
                                'data': json.dumps(space),
                                'id': space['id'],
                                'etag': space['etag']
                            })

                            logger.error("An error occured updating labstats spot %s: %s", (space.name, str(ex)))


                except Exception as ex:
                    for space in labstats_spaces:
                        if space['extended_info']['auto_labstats_available'] or space['extended_info']['auto_labstats_available'] == 0:
                            del space['extended_info']['auto_labstats_available']
                        if space['extended_info']['auto_labstats_total'] or space['extended_info']['auto_labstats_total'] == 0:
                            del space['extended_info']['auto_labstats_total']
                        if space['extended_info']['auto_labstats_off'] or space['extended_info']['auto_labstats_off'] == 0:
                            del space['extended_info']['auto_labstats_off']

                        upload_spaces.append({
                            'data': json.dumps(space),
                            'id': space['id'],
                            'etag': space['etag']
                        })

                    logger.error("Error getting labstats stats: %s", str(ex))

            except Exception as ex:
                logger.error("Error making the get request to the server: %s", str(ex))

            response = upload_data(upload_spaces)

            # If there are errors, log them
            if response['failure_descs']:
                errors = {}
                for failure in response['failure_descs']:
                    if type(failure['freason']) == list:
                        errors.update({failure['flocation']: []})
                        for reason in failure['freason']:
                            errors[failure['flocation']].append(reason)
                    else:
                        errors.update({failure['flocation']: failure['freason']})

                logger.error("Errors putting to the server: %s", str(errors))

            if not run_once:
                for i in range(update_delay * 60):
                    if self.should_stop():
                        sys.exit()
                    else:
                        time.sleep(1)

            else:
                sys.exit()

    def read_pid_file(self):
        if os.path.isfile(self._get_pid_file_path()):
            return True
        return False

    def create_pid_file(self):
        handle = open(self._get_pid_file_path(), 'w')
        handle.write(str(os.getpid()))
        handle.close()
        return

    def create_stop_file(self):
        handle = open(self._get_stopfile_path(), 'w')
        handle.write(str(os.getpid()))
        handle.close()
        return

    def remove_pid_file(self):
        os.remove(self._get_pid_file_path())

        if os.path.isfile(self._get_stopfile_path()):
            self.remove_stop_file()

    def remove_stop_file(self):
        os.remove(self._get_stopfile_path())

    # Returns true if an instance of the daemon is already running
    def process_exists(self):
        try:
            files = os.listdir("/tmp/updater")
        except OSError:
            sys.exit(0)
        for filename in files:
            matches = re.match(r"^([0-9]+).pid$", filename)
            if matches:
                return True
        return False

    def _get_pid_file_path(self):
        if not os.path.isdir("/tmp/updater/"):
            os.mkdir("/tmp/updater/", 0700)
        return "/tmp/updater/%s.pid" % (str(os.getpid()))

    def should_stop(self):
        if os.path.isfile(self._get_stopfile_path()):
            self.remove_stop_file()
            return True
        return False

    def _get_stopfile_path(self):
        if not os.path.isdir("/tmp/updater/"):
            os.mkdir("/tmp/updater/", 0700)
        return "/tmp/updater/%s.stop" % (str(os.getpid()))
