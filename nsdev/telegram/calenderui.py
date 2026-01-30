import calendar
from datetime import datetime

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class CalendarUI:
    def __init__(self, language: str = "id"):
        if language == "id":
            self.days = ["Sn", "Sl", "Rb", "Km", "Jm", "Sb", "Mg"]
            self.months = [
                "Januari",
                "Februari",
                "Maret",
                "April",
                "Mei",
                "Juni",
                "Juli",
                "Agustus",
                "September",
                "Oktober",
                "November",
                "Desember",
            ]
        else:
            self.days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            self.months = [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]

    def create_calendar(self, year: int = None, month: int = None):
        now = datetime.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month

        keyboard = []

        month_name = self.months[month - 1]
        header_row = [
            InlineKeyboardButton("«", callback_data=f"CALENDAR|PREV|{year}|{month}"),
            InlineKeyboardButton(f"{month_name} {year}", callback_data="CALENDAR|IGNORE"),
            InlineKeyboardButton("»", callback_data=f"CALENDAR|NEXT|{year}|{month}"),
        ]
        keyboard.append(header_row)

        week_header = [InlineKeyboardButton(day, callback_data="CALENDAR|IGNORE") for day in self.days]
        keyboard.append(week_header)

        month_calendar = calendar.monthcalendar(year, month)
        for week in month_calendar:
            row = []
            for day in week:
                if day == 0:
                    row.append(InlineKeyboardButton(" ", callback_data="CALENDAR|IGNORE"))
                else:
                    row.append(InlineKeyboardButton(str(day), callback_data=f"CALENDAR|DAY|{year}|{month}|{day}"))
            keyboard.append(row)

        return InlineKeyboardMarkup(keyboard)

    def process_callback(self, callback_data: str):
        parts = callback_data.split("|")
        if len(parts) < 2 or parts[0] != "CALENDAR":
            return None, None

        action = parts[1]

        if action == "IGNORE":
            return "IGNORE", None

        if action == "DAY":
            year, month, day = int(parts[2]), int(parts[3]), int(parts[4])
            return "SELECTED", datetime(year, month, day)

        if action == "PREV" or action == "NEXT":
            year, month = int(parts[2]), int(parts[3])
            if action == "PREV":
                month -= 1
                if month < 1:
                    month = 12
                    year -= 1
            else:
                month += 1
                if month > 12:
                    month = 1
                    year += 1
            return "UPDATE", (year, month)

        return None, None
