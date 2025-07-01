class Button:
    def __init__(self):
        self.re = __import__("re")
        self.math = __import__("math")
        self.pyrogram = __import__("pyrogram")

    def get_urls(self, text):
        return self.re.findall(r"(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:[/?]\S+)?|tg://\S+$", text)

    def parse_buttons_and_text(self, text, mode="inline"):
        if mode == "inline":
            button_data = self.re.findall(r"\| ([^|]+) - ([^|]+) \|", text)
            extracted_text = self.re.split(r"\| [^|]+ - [^|]+ \|", text)[0].strip() if "|" in text else text.strip()
            return button_data, extracted_text

        elif mode == "reply":
            pattern = r"\|\s*([^\|]+?)\s*\|"
            raw_data = self.re.findall(pattern, text)
            extracted_text = self.re.sub(pattern, "", text).strip()

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

    def create_keyboard(self, text, inline_cmd=None, is_id=None):
        layout = []
        buttons, remaining_text = self.parse_buttons_and_text(text, mode="inline")

        for label, payload in buttons:
            cb_data, *extra_params = payload.split(";")

            if not self.get_urls(cb_data):
                cb_data = f"{inline_cmd} {is_id}_{cb_data}" if inline_cmd and is_id else cb_data

            if "user" in extra_params:
                button = self.pyrogram.types.InlineKeyboardButton(label, user_id=cb_data)
            elif self.get_urls(cb_data):
                button = self.pyrogram.types.InlineKeyboardButton(label, url=cb_data)
            else:
                button = self.pyrogram.types.InlineKeyboardButton(label, callback_data=cb_data)

            if "same" in extra_params and layout:
                layout[-1].append(button)
            else:
                layout.append([button])

        return self.pyrogram.types.InlineKeyboardMarkup(layout), remaining_text

    def create_reply_keyboard(self, text):
        layout = []
        buttons, remaining_text = self.parse_buttons_and_text(text, mode="reply")

        for label, params in buttons:
            button = self.pyrogram.types.KeyboardButton(label)
            if "same" in params and layout:
                layout[-1].append(button)
            else:
                layout.append([button])

        return self.pyrogram.types.ReplyKeyboardMarkup(layout, resize_keyboard=True), remaining_text

    def remove_reply_keyboard(self, selective=False):
        return self.pyrogram.types.ReplyKeyboardRemove(selective=selective)

    def build_button_grid(self, buttons, row_inline=None, row_width=2):
        row_inline = row_inline or {}

        grid = [[self.pyrogram.types.InlineKeyboardButton(**data) for data in buttons[i : i + row_width]] for i in range(0, len(buttons), row_width)]

        if row_inline:
            grid.append([self.pyrogram.types.InlineKeyboardButton(**row_inline)])

        return self.pyrogram.types.InlineKeyboardMarkup(grid)
