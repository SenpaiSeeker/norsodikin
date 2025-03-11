class LoggerHandler:
    def __init__(self, **options):
        """
        Inisialisasi logger dengan parameter opsional.

        :param options:
            - log_level: Level log (default: 'DEBUG')
            - tz: Zona waktu untuk waktu lokal (default: 'Asia/Jakarta')
            - fmt: Format log (default: '{asctime} {levelname} {module}:{funcName}:{lineno} {message}')
            - datefmt: Format tanggal dan waktu (default: '%Y-%m-%d %H:%M:%S')
        """
        self.LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.sys = __import__("sys")
        self.os = __import__("os")

        self.log_level = self.LEVELS.get(options.get("log_level", "DEBUG").upper(), 20)
        self.tz = self.zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.fmt = options.get("fmt", "{asctime} {levelname} {module}:{funcName}:{lineno} {message}")
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S")

    def get_colors(self):
        return {
            "INFO": "\033[1;38;5;46m",  # Green maksimal (0,5,0)
            "DEBUG": "\033[1;38;5;21m",  # Blue murni (0,0,5)
            "WARNING": "\033[1;38;5;226m",  # Yellow murni (5,5,0)
            "ERROR": "\033[1;38;5;196m",  # Red murni (5,0,0)
            "CRITICAL": "\033[1;38;5;201m",  # Magenta murni (5,0,5)
            "TIME": "\033[1;38;5;231m",  # White penuh (5,5,5)
            "MODULE": "\033[1;38;5;51m",  # Cyan murni (0,5,5)
            "PIPE": "\033[1;38;5;93m",  # Ungu terang untuk simbol '|'
            "RESET": "\033[0m",
        }

    def formatTime(self, record):
        utc_time = self.datetime.datetime.utcfromtimestamp(record["created"])
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record, isNoModuleLog=False):
        level_color = self.get_colors().get(record["levelname"], self.get_colors()["RESET"])
        pipe_color = self.get_colors()["PIPE"]

        record["levelname"] = f"{pipe_color}|{self.get_colors()['RESET']} {level_color}{record['levelname']:<8}"
        record["message"] = f"{pipe_color}|{self.get_colors()['RESET']} {level_color}{record['message']}{self.get_colors()['RESET']}"

        formatted_time = self.formatTime(record)

        if isNoModuleLog:
            fmt = "{asctime} {levelname} {message}"
            return fmt.format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                levelname=record["levelname"],
                message=record["message"],
            )
        else:
            return self.fmt.format(
                asctime=f"{self.get_colors()['TIME']}[{formatted_time}]",
                levelname=record["levelname"],
                module=f"{pipe_color}|{self.get_colors()['RESET']} {self.get_colors()['MODULE']}{self.os.path.basename(record.get('module', '<unknown>'))}",
                funcName=record.get("funcName", "<unknown>"),
                lineno=record.get("lineno", 0),
                message=record["message"],
            )

    def log(self, level, message, isNoModuleLog=False):
        if self.LEVELS.get(level, 0) >= self.log_level:
            frame = self.sys._getframe(2)
            filename = self.os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
            record = {
                "created": self.datetime.datetime.now().timestamp(),
                "levelname": level,
                "module": filename if not isNoModuleLog else "",
                "funcName": frame.f_code.co_name if not isNoModuleLog else "",
                "lineno": frame.f_lineno if not isNoModuleLog else "",
                "message": message,
            }
            formatted_message = self.format(record, isNoModuleLog=isNoModuleLog)
            print(formatted_message)

    def debug(self, message, isNoModuleLog=False):
        self.log("DEBUG", message, isNoModuleLog=isNoModuleLog)

    def info(self, message, isNoModuleLog=False):
        self.log("INFO", message, isNoModuleLog=isNoModuleLog)

    def warning(self, message, isNoModuleLog=False):
        self.log("WARNING", message, isNoModuleLog=isNoModuleLog)

    def error(self, message, isNoModuleLog=False):
        self.log("ERROR", message, isNoModuleLog=isNoModuleLog)

    def critical(self, message, isNoModuleLog=False):
        self.log("CRITICAL", message, isNoModuleLog=isNoModuleLog)
