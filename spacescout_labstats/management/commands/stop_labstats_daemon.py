"""
This provides a management command that stops the labstats daemon
"""
from django.core.management.base import BaseCommand
from optparse import make_option
from spacescout_labstats.utils import _get_tmp_directory
import time
import signal
import os
import sys
import re
import stop_process


class Command(BaseCommand):
    help = "This stops any running labstats updaters."

    option_list = BaseCommand.option_list + (
        make_option('--force',
                    dest='force',
                    default=False,
                    action="store_true",
                    help='This will forceably terminate any running updaters. '
                         'Not recommended.'),

        make_option('--verbose',
                    dest='verbose',
                    default=False,
                    action='store_true',
                    help='print out detailed log in console'),
    )

    def handle(self, *args, **options):
        force = options["force"]

        try:
            files = os.listdir(_get_tmp_directory())
        except OSError:
            logger.error("OSError encountered when attempting to get " +
                         "temporary files. Daemon could not be stopped")
            sys.exit(0)

        # get the file with the PID of the other labstats daemons
        for filename in files:
            matches = re.match(r"^([0-9]+).pid$", filename)
            if matches:
                pid = matches.group(1)
                if force:
                    self.kill_process(pid)
                else:
                    verbose = options["verbose"]
                    if stop_process.stop_process(pid, verbose):
                        sys.exit(0)
                    else:
                        sys.exit(1)

    def kill_process(self, pid):
        """
        Kills the process with the passed PID and removes its PID file.
        """
        try:
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)

            try:
                os.getpgid(int(pid))
                os.kill(int(pid), signal.SIGKILL)
            except:
                pass
            if os.path.isfile(_get_tmp_directory() + "%s.stop" % pid):
                os.remove(_get_tmp_directory() + "%s.stop" % pid)

            if os.path.isfile(_get_tmp_directory() + "%s.pid" % pid):
                os.remove(_get_tmp_directory() + "%s.pid" % pid)
        except:
            pass
