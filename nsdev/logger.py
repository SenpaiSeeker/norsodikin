import datetime
import logging
import sys

import pytz

COLORS = {
    "INFO": "\033[1;92m",  # Full Bright Green
    "DEBUG": "\033[1;94m",  # Full Bright Blue
    "WARNING": "\033[1;93m",  # Full Bright Yellow
    "ERROR": "\033[1;91m",  # Full Bright Red
    "CRITICAL": "\033[1;95m",  # Full Bright Magenta
    "RESET": "\033[0m",  # Reset color
}


class ColoredFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        timezone = pytz.timezone("Asia/Jakarta")
        utc_time = datetime.datetime.utcfromtimestamp(record.created).replace(tzinfo=pytz.utc)
        local_time = utc_time.astimezone(timezone)

        return local_time.strftime(datefmt) if datefmt else local_time.strftime("%Y-%m-%d %H:%M:%S")

    def format(self, record):
        level_color = COLORS.get(record.levelname, COLORS.get("RESET"))
        record.levelname = f"{level_color}| {record.levelname:<8}{COLORS.get('RESET')}"
        return super().format(record)


class LoggerHandler:
    def __init__(self, log_level=logging.INFO):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        formatter = ColoredFormatter(
            "\033[1;97m[%(asctime)s] %(levelname)s \033[1;96m| %(module)s:%(funcName)s:%(lineno)d\033[0m %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        self.logger.addHandler(stream_handler)

    def debug(self, message):
        self.send_message("DEBUG", message)

    def info(self, message):
        self.send_message("INFO", message)

    def warning(self, message):
        self.send_message("WARNING", message)

    def error(self, message):
        self.send_message("ERROR", message)

    def critical(self, message):
        self.send_message("CRITICAL", message)

    def send_message(self, log_type: str, message: str):
        log_function = getattr(self.logger, log_type.lower(), self.logger.warning)
        color = COLORS.get(log_type, COLORS["RESET"])
        log_function(f"{color}| {message}{COLORS['RESET']}")
