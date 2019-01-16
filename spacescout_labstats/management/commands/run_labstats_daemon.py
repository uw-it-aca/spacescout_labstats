"""
This provides a managament command to run a daemon that will frequently update
the spaces that have corresponding labstats information with the number of
machines available and similar information.
"""
from django.core.management.base import BaseCommand
from spacescout_labstats import utils
from django.conf import settings
from optparse import make_option
from spacescout_labstats.endpoints import online_labstats, cte_techloan
import os
import sys
import time
import re
import atexit
import oauth2
import json
import traceback
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'This updates spaces with labstats data'

    option_list = BaseCommand.option_list + (
        make_option('--daemonize',
                    dest='daemon',
                    default=True,
                    action='store_true',
                    help='This will set the updater to run as a daemon.'),

        make_option('--interactive',
                    dest='daemon',
                    action='store_false',
                    help='This will set the updater to run interactively.'),

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
            # TODO : refactor into utils/utils.stop_process for DRY
            try:
                files = os.listdir(utils._get_tmp_directory())
            except OSError:
                logger.warning("OSError encountered when attempting to get " +
                               "temporary files.")
            for filename in files:
                # check for file containing pid
                matches = re.match(r"^([0-9]+).pid$", filename)
                # if it exists, then stop the process
                if matches:
                    pid = matches.group(1)
                    verbose = options["verbose"]
                    logger.info("Stopping an existing labstats_daemon")
                    utils.stop_process(pid, verbose)

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
                logger.error("Uncaught error running the controller",
                             exc_info=1)

        else:
            logger.info("Starting the updater as an interactive process")
            self.create_pid_file()
            self.controller(options["update_delay"], options["run_once"])

    def controller(self, update_delay, run_once=False):
        """
        This is responsible for the workflow of orchestrating
        the updater process.
        """
        if not hasattr(settings, 'SS_WEB_SERVER_HOST'):
            raise(Exception("Required setting missing: SS_WEB_SERVER_HOST"))

        if not hasattr(settings, 'SS_WEB_OAUTH_KEY'):
            raise(Exception("Required setting missing: SS_WEB_OAUTH_KEY"))

        if not hasattr(settings, 'SS_WEB_OAUTH_SECRET'):
            raise(Exception("Required setting missing: SS_WEB_OAUTH_SECRET"))

        self.consumer = oauth2.Consumer(key=settings.SS_WEB_OAUTH_KEY,
                                        secret=settings.SS_WEB_OAUTH_SECRET)
        self.client = oauth2.Client(self.consumer)

        while True:
            if self.should_stop():
                sys.exit()

            # This allows for a one time run via interactive process for
            # automated testing
            if run_once:
                self.create_stop_file()

            # add any additional endpoints here and at the import statement
            # at the top of this file
            endpoints = [online_labstats, cte_techloan]

            for endpoint in endpoints:
                try:
                    self.load_endpoint_data(endpoint)
                except Exception as ex:
                    logger.error("Uncaught exception for endpoint, " +
                                 endpoint.get_name(), exc_info=1)

            # then wait for update_delay minutes (default 15)
            if not run_once:
                for i in range(update_delay * 60):
                    if self.should_stop():
                        sys.exit()
                    else:
                        time.sleep(1)
            else:
                sys.exit()

    def load_endpoint_data(self, endpoint):
        """
        This method handles the updating of an endpoint using the standard
        interface.
        """
        try:
            url = endpoint.get_space_search_parameters()
            resp, content = self.client.request(url, 'GET')

            if(resp.status == 401):
                logger.error("Labstats daemon has outdated OAuth credentials!")
                return

            spaces = json.loads(content)

        except ValueError as ex:
            logger.warning("JSON Exception found! Malformed data passed from"
                           "spotseeker_server", exc_info=1)
            return

        to_remove = []
        # validate spaces against utils.validate_space
        for space in spaces:
            if not utils.validate_space(space):
                to_remove.append(space)

        # remove noncompliant spaces
        for space in to_remove:
            spaces.remove(space)

        # get spaces that don't follow the endpoint standards
        to_clean = []

        for space in spaces:
            try:
                endpoint.validate_space(space)
            except Exception as ex:
                logger.warning("Space invalid", exc_info=1)
                utils.clean_spaces_labstats([space])
                to_clean.append(space)

        # if our endpoint rejects spaces, then save them until after the update
        for space in to_clean:
            spaces.remove(space)

        # send the spaces to be modified to the endpoint

        endpoint.get_endpoint_data(spaces)

        # add the to_clean spaces back in
        for space in to_clean:
            spaces.append(space)

        # upload the space data to the server
        response = utils.upload_data(spaces)

        # log any failures
        if response is not None and response['failure_descs']:
            errors = {}
            for failure in response['failure_descs']:
                if isinstance(failure['freason'], list):
                    errors.update({failure['flocation']: []})
                    for reason in failure['freason']:
                        errors[failure['flocation']].append(reason)
                else:
                    errors.update({failure['flocation']:
                                   failure['freason']})

            logger.warning("Errors putting to the server: %s", str(errors))

    def read_pid_file(self):
        return os.path.isfile(self._get_pid_file_path())

    def create_pid_file(self):
        with open(self._get_pid_file_path(), 'w') as handle:
            handle.write(str(os.getpid()))

    def create_stop_file(self):
        with open(self._get_stopfile_path(), 'w') as handle:
            handle.write(str(os.getpid()))

    def remove_pid_file(self):
        os.remove(self._get_pid_file_path())

        if os.path.isfile(self._get_stopfile_path()):
            self.remove_stop_file()

    def remove_stop_file(self):
        os.remove(self._get_stopfile_path())

    # Returns true if an instance of the daemon is already running
    def process_exists(self):
        try:
            files = os.listdir(utils._get_tmp_directory())
        except OSError:
            sys.exit(0)

        for filename in files:
            matches = re.match(r"^([0-9]+).pid$", filename)
            if matches:
                return True
        return False

    # Returns the path for the file storing this process' PID
    def _get_pid_file_path(self):
        return utils._get_tmp_directory() + "%s.pid" % (str(os.getpid()))

    def should_stop(self):
        if os.path.isfile(self._get_stopfile_path()):
            self.remove_stop_file()
            return True
        return False

    def _get_stopfile_path(self):
        return utils._get_tmp_directory() + "%s.stop" % (str(os.getpid()))
