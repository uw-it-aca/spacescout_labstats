"""
This function stops the labstats daemon
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


def stop_process(pid, verbose):
    if verbose:
        print "Stopping process: %s" % pid
    try:
        handle = open("/tmp/updater/%s.stop" % pid, "w")
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
            os.remove("/tmp/updater/%s.stop" % pid)
            if verbose:
                print " Process did not end"
            return False
    except OSError:
        os.remove(("/tmp/updater/%s.pid" % pid))
        os.remove(("/tmp/updater/%s.stop" % pid))
        if verbose:
            print "Old process %s not Found" % pid
    return True
