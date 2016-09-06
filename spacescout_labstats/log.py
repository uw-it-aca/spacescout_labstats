import logging
import traceback

from django.conf import settings
from django.core import mail
from django.views.debug import ExceptionReporter, get_exception_reporter_filter

# Make sure a NullHandler is available
# This was added in Python 2.7/3.2
try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

# Make sure that dictConfig is available
# This was added in Python 2.7/3.2
try:
    from logging.config import dictConfig
except ImportError:
    from django.utils.dictconfig import dictConfig

getLogger = logging.getLogger

# Ensure the creation of the Django logger
# with a null handler. This ensures we don't get any
# 'No handlers could be found for logger "django"' messages
logger = getLogger('django')
if not logger.handlers:
    logger.addHandler(NullHandler())


class UpdaterEmailHandler(logging.Handler):
    """An exception log handler that emails log entries to site admins.
    If the request is passed as the first argument to the log record,
    request data will be provided in the email report.
    """

    def __init__(self, include_html=False):
        logging.Handler.__init__(self)
        self.include_html = include_html

    def emit(self, record):
        error = record.getMessage()

        subject = '%s: %s' % (
            record.levelname,
            error
        )

        if record.exc_info is not None:
            message = '\n'.join(traceback.format_exception(*record.exc_info))
        else:
            message = "No stack trace provided"

        mail.mail_admins(subject, message, fail_silently=True)

    def format_subject(self, subject):
        """
        Escape CR and LF characters, and limit length.
        RFC 2822's hard limit is 998 characters per line. So, minus "Subject: "
        the actual subject must be no longer than 989 characters.
        """
        formatted_subject = subject.replace('\n', '\\n').replace('\r', '\\r')
        return formatted_subject[:989]
