import sys
import inspect
from datetime import datetime
from pytz import timezone, utc

COLORS = {
    "INFO": "\033[1;92m",
    "DEBUG": "\033[1;94m",
    "WARNING": "\033[1;93m",
    "ERROR": "\033[1;91m",
    "CRITICAL": "\033[1;95m",
    "TIME": "\033[1;97m",
    "RESET": "\033[0m",
}

class CustomFormatter:
    def __init__(self, fmt=None, datefmt=None, tz="Asia/Jakarta"):
        self.fmt = fmt or "%(asctime)s %(levelname)s %(module)s:%(funcName)s:%(lineno)d %(message)s"
        self.datefmt = datefmt or "%Y-%m-%d %H:%M:%S"
        self.tz = timezone(tz)

    def formatTime(self, record):
        utc_time = datetime.utcfromtimestamp(record["created"]).replace(tzinfo=utc)
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record):
        level_color = COLORS.get(record["levelname"], COLORS["RESET"])
        record["levelname"] = f"{level_color}| {record['levelname']:<8}{COLORS['RESET']}"
        record["message"] = f"{level_color}| {record['message']}{COLORS['RESET']}"
        
        formatted_time = self.formatTime(record)
        return self.fmt % {
            "asctime": f"{COLORS['TIME']}[{formatted_time}]{COLORS['RESET']}",
            "levelname": record["levelname"],
            "module": f"\033[1;96m| {record.get('module', '<unknown>')}",
            "funcName": record.get('funcName', '<unknown>'),
            "lineno": record.get('lineno', 0),
            "message": record["message"]
        }

class LoggerHandler:
    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}

    def __init__(self, log_level="DEBUG", tz="Asia/Jakarta"):
        self.log_level = self.LEVELS.get(log_level.upper(), 20)
        self.formatter = CustomFormatter(tz=tz)

    def log(self, level, message):
        if self.LEVELS[level] >= self.log_level:
            frame = inspect.currentframe().f_back
            record = {
                "created": datetime.now().timestamp(),
                "levelname": level,
                "module": frame.f_globals.get("__name__", "<unknown>"),
                "funcName": frame.f_code.co_name,
                "lineno": frame.f_lineno,
                "message": message,
            }
            formatted_message = self.formatter.format(record)
            print(formatted_message, file=sys.stdout)

    def debug(self, message):
        self.log("DEBUG", message)

    def info(self, message):
        self.log("INFO", message)

    def warning(self, message):
        self.log("WARNING", message)

    def error(self, message):
        self.log("ERROR", message)

    def critical(self, message):
        self.log("CRITICAL", message)

if __name__ == "__main__":
    logger = LoggerHandler(log_level="DEBUG")

    logger.debug("Ini adalah pesan debug.")
    logger.info("Ini adalah pesan info.")
    logger.warning("Ini adalah pesan peringatan.")
    logger.error("Ini adalah pesan error.")
    logger.critical("Ini adalah pesan kritis.")
