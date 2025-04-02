class LoggerHandler(__import__("nsdev").AnsiColors):
    def __init__(self, **options):
        super().__init__()
        """
        Inisialisasi logger dengan parameter opsional.

        :param options:
            - tz: Zona waktu untuk waktu lokal (default: 'Asia/Jakarta')
            - fmt: Format log (default: '{asctime} {levelname} {module}:{funcName}:{lineno} {message}')
            - datefmt: Format tanggal dan waktu (default: '%Y-%m-%d %H:%M:%S')
        """
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.sys = __import__("sys")
        self.os = __import__("os")

        self.tz = self.zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.fmt = options.get("fmt", "{asctime} {levelname} {module}:{funcName}:{lineno} {message}")
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S %Z")

    def get_colors(self):
        return {
            "INFO": self.GREEN,
            "DEBUG": self.BLUE,
            "WARNING": self.YELLOW,
            "ERROR": self.RED,
            "CRITICAL": self.MAGENTA,
            "TIME": self.WHITE,
            "MODULE": self.CYAN,
            "PIPE": self.PURPLE,
            "RESET": self.RESET,
        }

    def formatTime(self):
        utc_time = self.datetime.datetime.utcfromtimestamp(self.datetime.datetime.now().timestamp())
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def format(self, record):
        level_color = self.get_colors().get(record["levelname"], self.RESET)
        pipe_color = self.get_colors()["PIPE"]

        record["levelname"] = f"{pipe_color}| {level_color}{record['levelname']:<8}"
        record["message"] = f"{pipe_color}| {level_color}{record['message']}{self.RESET}"

        return self.fmt.format(
            asctime=f"{self.get_colors()['TIME']}[ {self.formatTime()} ]",
            levelname=record["levelname"],
            module=f"{pipe_color}| {self.get_colors()['MODULE']}{self.os.path.basename(record.get('module', '<unknown>'))}",
            funcName=record.get("funcName", "<unknown>"),
            lineno=record.get("lineno", 0),
            message=record["message"],
        )

    def log(self, level, message):
        frame = self.sys._getframe(2)
        filename = self.os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
        record = {
            "levelname": level,
            "module": filename,
            "funcName": frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "message": message,
        }
        formatted_message = self.format(record)
        print(formatted_message)

    def print(self, message, isPrint=True):
        text = f"{self.CYAN}[ {self.WHITE}{self.formatTime()} {self.CYAN}] {self.WHITE}| {message}{self.RESET}"
        if isPrint:
            print(text)
        else:
            return text

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
