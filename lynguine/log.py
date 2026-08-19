import os
import logging

from lynguine.security.secure_logging import SanitizingFormatter

_LOG_FORMAT = "%(levelname)s:%(name)s:%(asctime)s:%(message)s"
_SANITIZER = SanitizingFormatter(fmt=_LOG_FORMAT)


def _sanitize_log_message(message):
    """Sanitize a log message so secrets are not written as clear text."""
    if message is None:
        return ""
    return _SANITIZER.sanitize(str(message))


class Logger:
    def __init__(self, name=None, level=20, filename=None, directory="."):
        if filename is None:
            filename = __name__
        if level == "debug":
            self.level = logging.DEBUG
        elif level == "info":
            self.level = logging.INFO
        elif level == "warning":
            self.level = logging.WARNING
        elif level == "error":
            self.level = logging.ERROR
        elif level == "critical":
            self.level = logging.CRITICAL
        else:
            # For backwards compatability allowing direct specificaiton of a numeric level
            self.level = level

        self.filename = filename
        self.name = name
        log_path = os.path.join(directory, filename)
        logging.basicConfig(
            level=self.level, filename=log_path, format=_LOG_FORMAT
        )
        self.logger = logging.getLogger(name)
        for handler in logging.root.handlers:
            handler.setFormatter(_SANITIZER)
        for handler in self.logger.handlers:
            handler.setFormatter(_SANITIZER)

    def debug(self, message):
        self.logger.debug(_sanitize_log_message(message))

    def info(self, message):
        self.logger.info(_sanitize_log_message(message))

    def warning(self, message):
        self.logger.warning(_sanitize_log_message(message))

    def error(self, message):
        self.logger.error(_sanitize_log_message(message))

    def critical(self, message):
        self.logger.critical(_sanitize_log_message(message))
