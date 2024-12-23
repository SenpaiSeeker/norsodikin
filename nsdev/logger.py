COLORS = {
    "INFO": "\033[1;92m",
    "DEBUG": "\033[1;94m",
    "WARNING": "\033[1;93m",
    "ERROR": "\033[1;91m",
    "CRITICAL": "\033[1;95m",
    "RESET": "\033[0m",
}


class Formatter(__import__("logging").Formatter):
    def __init__(self):
        self.datetime = __import__("datetime")
        self.pytz = __import__("pytz")
        super().__init__()

    def formatTime(self, record, datefmt=None):
        timezone = self.pytz.timezone("Asia/Jakarta")
        utc_time = self.datetime.datetime.utcfromtimestamp(record.created).replace(tzinfo=self.pytz.utc)
        local_time = utc_time.astimezone(timezone)

        return local_time.strftime(datefmt) if datefmt else local_time.strftime("%Y-%m-%d %H:%M:%S")

    def format(self, record):
        level_color = COLORS.get(record.levelname, COLORS.get("RESET"))
        record.levelname = f"{level_color}| {record.levelname:<8}{COLORS.get('RESET')}"
        return super().format(record)


class LoggerHandler:
    def __init__(self, log_level=None):
        self.logging = __import__("logging")
        self.sys = __import__("sys")

        log_level = log_level or self.logging.INFO
        self.logger = self.logging.getLogger(__name__)
        self.logger.setLevel(log_level)

        formatter = Formatter()
        formatter._style._fmt = "\033[1;97m[%(asctime)s] %(levelname)s \033[1;96m| %(module)s:%(funcName)s:%(lineno)d\033[0m %(message)s"

        stream_handler = self.logging.StreamHandler(self.sys.stdout)
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
