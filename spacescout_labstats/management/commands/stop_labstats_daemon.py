"""
This provides a management command that stops the labstats daemon
"""
from django.core.management.base import BaseCommand
from optparse import make_option
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
            files = os.listdir(self._get_tmp_directory())
        except OSError:
            sys.exit(0)
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
        try:
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)
            try:
                os.getpgid(int(pid))
                os.kill(int(pid), signal.SIGKILL)
            except:
                pass
            if os.path.isfile(self._get_tmp_directory() + "%s.stop" % pid):
                os.remove(self._get_tmp_directory() + "%s.stop" % pid)

            if os.path.isfile(self._get_tmp_directory() + "%s.pid" % pid):
                os.remove(self._get_tmp_directory() + "%s.pid" % pid)
        except:
            pass

    # Returns the directory in which labstats temp files will be stored, and
    # creates it if it does not exist
    def _get_tmp_directory(self):
        if not os.path.isdir("/tmp/updater/"):
            os.mkdir("/tmp/updater/", 0700)
            return "/tmp/updater/"
