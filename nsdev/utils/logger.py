import datetime
import logging
import os
import sys
import zoneinfo
from typing import Optional

from .colorize import AnsiColors


class LoggerHandler(AnsiColors):
    def __init__(self, **options):
        super().__init__()
        self.tz = zoneinfo.ZoneInfo(options.get("tz", "Asia/Jakarta"))
        self.datefmt = options.get("datefmt", "%Y-%m-%d %H:%M:%S %Z")
        self.show_emoji = options.get("show_emoji", True)
        
        self.colors = {
            "INFO": self.LIGHT_GREEN,
            "DEBUG": self.LIGHT_BLUE,
            "WARNING": self.LIGHT_YELLOW,
            "ERROR": self.LIGHT_RED,
            "CRITICAL": self.LIGHT_MAGENTA,
            "SUCCESS": self.LIGHT_GREEN,
            "TIME": self.WHITE,
            "MODULE": self.LIGHT_CYAN,
            "FUNC": self.LIGHT_PURPLE,
            "LINE": self.LIGHT_ORANGE,
            "PIPE": self.LIGHT_GRAY,
            "BOX": self.LIGHT_GRAY,
            "RESET": self.RESET,
            "TEXT": self.LIGHT_WHITE
        }
        
        self.box = {
            "tl": "╭",
            "tr": "╮",
            "bl": "╰",
            "br": "╯",
            "h": "─",
            "v": "│",
            "sep": "├─",
            "obr": "[ ",
            "cbr": " ]",
            "pipe": "|"
        }

    def formatTime(self) -> str:
        utc_time = datetime.datetime.now(datetime.timezone.utc)
        local_time = utc_time.astimezone(self.tz)
        return local_time.strftime(self.datefmt)

    def _get_terminal_width(self) -> int:
        try:
            return os.get_terminal_size().columns
        except OSError:
            return 80

    def format(self, record: dict) -> str:
        level = record["levelname"]
        message = record["message"]
        module = record.get("module", "<unknown>")
        func = record.get("funcName", "<unknown>")
        line = record.get("lineno", 0)
        
        width = min(self._get_terminal_width(), 100)
        timestamp = self.formatTime()
        
        box_c = self.colors["BOX"]
        time_c = self.colors["TIME"]
        lvl_c = self.colors.get(level, self.LIGHT_GREEN)
        mod_c = self.colors["MODULE"]
        func_c = self.colors["FUNC"]
        ln_c = self.colors["LINE"]
        pipe_c = self.colors["PIPE"]
        text_c = self.colors["TEXT"]
        rst = self.colors["RESET"]

        top_bar_len = width - len(timestamp) - 7
        if top_bar_len < 0: top_bar_len = 0
        
        header = (
            f"{box_c}{self.box['tl']}{self.box['h']}{self.box['obr']}"
            f"{time_c}{timestamp}{rst}"
            f"{box_c}{self.box['cbr']}{self.box['h'] * top_bar_len}{self.box['tr']}{rst}"
        )
        
        content = (
            f"{box_c}{self.box['sep']} {self.box['obr']}"
            f"{lvl_c}{level}{rst}"
            f"{box_c}{self.box['cbr']} "
            f"{pipe_c}{self.box['pipe']} "
            f"{mod_c}{module}{rst}:"
            f"{func_c}{func}{rst}:"
            f"{ln_c}{line}{rst} "
            f"{pipe_c}{self.box['pipe']} "
            f"{lvl_c}{message}{rst}"
        )
        
        footer = f"{box_c}{self.box['bl']}{self.box['h'] * (width - 2)}{self.box['br']}{rst}"
        
        return f"{header}\n{content}\n{footer}"

    def print(self, message: str, isPrint: bool = True) -> Optional[str]:
        width = min(self._get_terminal_width(), 100)
        timestamp = self.formatTime()
        
        box_c = self.colors["BOX"]
        time_c = self.colors["TIME"]
        text_c = self.colors["TEXT"]
        rst = self.colors["RESET"]

        top_bar_len = width - len(timestamp) - 8
        if top_bar_len < 0: top_bar_len = 0

        text = (
            f"{box_c}{self.box['tl']}{self.box['h']}{self.box['obr']}"
            f"{time_c}{timestamp}{rst}"
            f"{box_c}{self.box['cbr']}{self.box['h'] * top_bar_len}{self.box['tr']}\n"
            f"{box_c}{self.box['sep']} {text_c}{message}{rst}\n"
            f"{box_c}{self.box['bl']}{self.box['h'] * (width - 2)}{self.box['br']}{rst}"
        )
        
        if isPrint:
            print(f"\033[2K{text}")
        else:
            return text

    def banner(self, title: str, subtitle: str = ""):
        width = min(self._get_terminal_width(), 80)
        box_c = self.colors["BOX"]
        title_c = self.colors["LIGHT_CYAN"]
        sub_c = self.colors["WHITE"]
        rst = self.colors["RESET"]
        
        print(f"\n{box_c}{self.box['tl']}{self.box['h'] * (width - 2)}{self.box['tr']}")
        print(f"{box_c}{self.box['v']}{title_c}{title.center(width - 2)}{rst}{box_c}{self.box['v']}")
        if subtitle:
            print(f"{box_c}{self.box['v']}{sub_c}{subtitle.center(width - 2)}{rst}{box_c}{self.box['v']}")
        print(f"{box_c}{self.box['bl']}{self.box['h'] * (width - 2)}{self.box['br']}{rst}\n")

    def separator(self, char: str = "─", color: str = None):
        width = min(self._get_terminal_width(), 80)
        col = color or self.colors["BOX"]
        print(f"{col}{char * width}{self.RESET}")

    def log(self, level: str, message: str):
        frame = sys._getframe(2)
        filename = os.path.basename(frame.f_globals.get("__file__", "<unknown>"))
        
        record = {
            "levelname": level,
            "module": filename.replace(".py", ""),
            "funcName": frame.f_code.co_name,
            "lineno": frame.f_lineno,
            "message": message,
        }
        
        formatted_message = self.format(record)
        print(f"\033[2K{formatted_message}")

    def debug(self, message: str):
        self.log("DEBUG", message)

    def info(self, message: str):
        self.log("INFO", message)

    def success(self, message: str):
        self.log("SUCCESS", message)

    def warning(self, message: str):
        self.log("WARNING", message)

    def error(self, message: str):
        self.log("ERROR", message)

    def critical(self, message: str):
        self.log("CRITICAL", message)


class CustomLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.formatter_util = LoggerHandler()

    def emit(self, record: logging.LogRecord):
        custom_record = {
            "levelname": record.levelname,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
            "message": record.getMessage(),
        }
        try:
            msg = self.formatter_util.format(custom_record)
            print(f"\033[2K{msg}")
        except Exception:
            self.handleError(record)
