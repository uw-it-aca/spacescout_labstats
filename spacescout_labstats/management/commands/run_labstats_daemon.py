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
from spacescout_labstats.endpoints.seattle_labstats import SeattleLabstats
import os
import sys
import time
import re
import atexit
import oauth2
import json
import logging
import stop_process

# TODO: how should the log location be set?
# logging.basicConfig(filename='/tmp/labstats_updater.log',
# level=logging.DEBUG, filemode='w')
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
        Before starting this daemon, this will check for another version of
        this process by checking for a file in the temporary folder, and then
        if another version exists it will close that process.
        """
        if (self.process_exists()):
            try:
                files = os.listdir(self._get_tmp_directory())
            except OSError:
                logger.error("OSError encountered when attempting to get " +
                             "temporary files")
                sys.exit(0)
            for filename in files:
                matches = re.match(r"^([0-9]+).pid$", filename)  # check if pid
                if matches:
                    pid = matches.group(1)
                    verbose = options["verbose"]
                    logger.info("stopping")
                    stop_process.stop_process(pid, verbose)

        atexit.register(self.remove_pid_file)

        daemon = options["daemon"]  # get the flag

        if daemon:
            logger.info("Starting the updater as a daemon")
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
            logger.info("Starting the updater as an interactive process")
            self.create_pid_file()
            self.controller(options["update_delay"], options["run_once"])

    def controller(self, update_delay, run_once=False):
        """
        This is responsible for the workflow of orchestrating
        the updater process.
        """
        # TODO : determine where this exception is handled
        if not hasattr(settings, 'SS_WEB_SERVER_HOST'):
            raise(Exception("Required setting missing: SS_WEB_SERVER_HOST"))

        if not hasattr(settings, 'SS_WEB_OAUTH_KEY'):
            raise(Exception("Required setting missing: SS_WEB_OAUTH_KEY"))

        if not hasattr(settings, 'SS_WEB_OAUTH_SECRET'):
            raise(Exception("Required setting missing: SS_WEB_OAUTH_SECRET"))

        consumer = oauth2.Consumer(key=settings.SS_WEB_OAUTH_KEY,
                                   secret=settings.SS_WEB_OAUTH_SECRET)
        client = oauth2.Client(consumer)

        while True:
            if self.should_stop():
                sys.exit()

            # This allows for a one time run via interactive process for
            # automated testing
            if run_once:
                self.create_stop_file()

            upload_spaces = []

            # raise different exceptions
            if not hasattr(settings, 'LS_CENTER_LAT'):
                raise(Exception("Required setting missing: LS_CENTER_LAT"))
            if not hasattr(settings, 'LS_CENTER_LON'):
                raise(Exception("Required setting missing: LS_CENTER_LON"))
            if not hasattr(settings, 'LS_SEARCH_DISTANCE'):
                raise(Exception("Required setting missing:"
                                "LS_SEARCH_DISTANCE"))

            # get data from SS server
            try:
                url = ("%s/api/v1/spot/?extended_info:has_labstats=true"
                       "&center_latitude=%s&center_longitude=%s&distance=%s"
                       "&limit=0") % \
                    (settings.SS_WEB_SERVER_HOST,
                     settings.LS_CENTER_LAT,
                     settings.LS_CENTER_LON,
                     settings.LS_SEARCH_DISTANCE)
                resp, content = client.request(url, 'GET')
                labstats_spaces = json.loads(content)

                upload_spaces =
                response = upload_data(upload_spaces)

            except Exception as ex:
                logger.error("Error making the get request to the server: %s",
                             str(ex))

            # If there are errors, log them
            if response['failure_descs']:
                errors = {}
                for failure in response['failure_descs']:
                    if type(failure['freason']) == list:
                        errors.update({failure['flocation']: []})
                        for reason in failure['freason']:
                            errors[failure['flocation']].append(reason)
                    else:
                        errors.update({failure['flocation']:
                                       failure['freason']})

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
        handle = open(self._get_pid_file_path(), 'w')  # return file object
        handle.write(str(os.getpid()))  # write process id into file
        handle.close()  # no longer writable and readable
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
            files = os.listdir(self._get_tmp_directory())
        except OSError:
            sys.exit(0)
        for filename in files:
            matches = re.match(r"^([0-9]+).pid$", filename)
            if matches:
                return True
        return False

    # Returns the path for the file storing this process' PID
    def _get_pid_file_path(self):
        return self._get_tmp_directory() + "%s.pid" % (str(os.getpid()))

    # Returns the directory in which labstats temp files will be stored, and
    # creates it if it does not exist
    def _get_tmp_directory(self):
        if not os.path.isdir("/tmp/updater/"):
            os.mkdir("/tmp/updater/", 0700)
        return "/tmp/updater/"

    def should_stop(self):
        if os.path.isfile(self._get_stopfile_path()):
            self.remove_stop_file()
            return True
        return False

    def _get_stopfile_path(self):
        return self._get_tmp_directory() + "%s.stop" % (str(os.getpid()))
