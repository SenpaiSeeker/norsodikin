import math
import re
from typing import Dict, List

import pyrogram


class Button:
    def get_urls(self, text):
        return re.findall(r"(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:[/?]\S+)?|tg://\S+$", text)

    def parse_buttons_and_text(self, text, mode="inline"):
        if mode == "inline":
            button_data = re.findall(r"\| ([^|]+) - ([^|]+) \|", text)
            extracted_text = re.split(r"\| [^|]+ - [^|]+ \|", text)[0].strip() if "|" in text else text.strip()
            return button_data, extracted_text

        elif mode == "reply":
            pattern = r"\|\s*([^\|]+?)\s*\|"
            raw_data = re.findall(pattern, text)
            extracted_text = re.sub(pattern, "", text).strip()
            buttons = []

            for chunk in raw_data:
                parts = chunk.split("-")
                for part in parts:
                    if ";" in part:
                        label, *params = part.split(";")
                        buttons.append((label.strip().strip("]"), [p.strip() for p in params]))
                    else:
                        buttons.append((part.strip().strip("]"), []))
            return buttons, extracted_text

        else:
            raise ValueError("Invalid parse mode. Use 'inline' or 'reply'.")

    def create_inline_keyboard(self, text, inline_cmd=None, is_id=None, cb_prefix=None):
        layout = []
        buttons, remaining_text = self.parse_buttons_and_text(text, mode="inline")

        for label, payload in buttons:
            cb_data, *extra_params = payload.split(";")
            is_webapp = "webapp" in extra_params
            is_url = bool(self.get_urls(cb_data)) and not is_webapp
            is_copy = "copy" in extra_params
            is_user = "user" in extra_params

            if not is_url and not is_copy and not is_user and not is_webapp:
                if cb_prefix:
                    cb_data = f"{cb_prefix}_{cb_data}"
                elif inline_cmd and is_id:
                    cb_data = f"{inline_cmd} {is_id}_{cb_data}"
                elif inline_cmd:
                    cb_data = f"{inline_cmd} {cb_data}"

            if is_user:
                button = pyrogram.types.InlineKeyboardButton(label, user_id=cb_data)

            elif is_copy:
                button = pyrogram.types.InlineKeyboardButton(label, copy_text=cb_data)

            elif is_webapp:
                button = pyrogram.types.InlineKeyboardButton(label, web_app=pyrogram.types.WebAppInfo(url=cb_data))

            elif is_url:
                button = pyrogram.types.InlineKeyboardButton(label, url=cb_data)

            else:
                button = pyrogram.types.InlineKeyboardButton(label, callback_data=cb_data)

            if "same" in extra_params and layout:
                layout[-1].append(button)
            else:
                layout.append([button])

        return pyrogram.types.InlineKeyboardMarkup(layout), remaining_text

    def create_button_keyboard(self, text):
        layout = []
        buttons, remaining_text = self.parse_buttons_and_text(text, mode="reply")

        for label, params in buttons:
            if "is_contact" in params:
                button = pyrogram.types.KeyboardButton(label, request_contact=True)
            else:
                button = pyrogram.types.KeyboardButton(label)

            if "same" in params and layout:
                layout[-1].append(button)
            else:
                layout.append([button])

        return pyrogram.types.ReplyKeyboardMarkup(layout, resize_keyboard=True), remaining_text

    def remove_reply_keyboard(self, selective=False):
        return pyrogram.types.ReplyKeyboardRemove(selective=selective)

    def build_button_grid(self, layout: List[List[Dict]]):
        keyboard = []
        for row_data in layout:
            row = []
            for button_info in row_data:
                if "web_app" in button_info:
                    button_info["web_app"] = pyrogram.types.WebAppInfo(url=button_info["web_app"])
                row.append(pyrogram.types.InlineKeyboardButton(**button_info))
            if row:
                keyboard.append(row)
        return pyrogram.types.InlineKeyboardMarkup(keyboard) if keyboard else None

    def create_pagination_keyboard(
        self,
        items: list,
        current_page: int,
        items_per_page: int = 5,
        items_per_row: int = 1,
        callback_prefix: str = "nav",
        item_callback_prefix: str = None,
        extra_params: list = None,
    ):
        if current_page < 1:
            current_page = 1

        total_items = len(items)
        total_pages = math.ceil(total_items / items_per_page) or 1
        current_page = min(current_page, total_pages)
        start_index = (current_page - 1) * items_per_page
        end_index = start_index + items_per_page
        page_items = items[start_index:end_index]

        item_buttons_data = [
            (
                {
                    "text": item.get("text"),
                    "callback_data": (
                        f"{item_callback_prefix}_{item.get('data')}" if item_callback_prefix else item.get("data")
                    ),
                }
                if isinstance(item, dict)
                else {
                    "text": str(item),
                    "callback_data": f"{item_callback_prefix}_{item}" if item_callback_prefix else str(item),
                }
            )
            for item in page_items
        ]

        layout_grid = [
            item_buttons_data[i : i + items_per_row] for i in range(0, len(item_buttons_data), items_per_row)
        ]

        nav_row_data = []
        if current_page > 1:
            nav_row_data.append({"text": "⬅️", "callback_data": f"{callback_prefix}_{current_page - 1}"})

        if total_pages > 1:
            nav_row_data.append({"text": f"[{current_page}/{total_pages}]", "callback_data": "noop"})

        if current_page < total_pages:
            nav_row_data.append({"text": "➡️", "callback_data": f"{callback_prefix}_{current_page + 1}"})

        if nav_row_data:
            layout_grid.append(nav_row_data)

        if extra_params:
            for button_data in extra_params:
                layout_grid.append([button_data])

        return self.build_button_grid(layout_grid)
