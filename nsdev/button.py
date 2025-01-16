class Button:
    def __init__(self):
        self.re = __import__("re")
        self.math = __import__("math")
        self.pyrogram = __import__("pyrogram")

        self.url_pattern = r"(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:[/?]\S+)?|tg://\S+$"

    def get_urls(self, text):
        return self.re.findall(self.url_pattern, text)

    def parse_buttons_and_text(self, text):
        button_data = self.re.findall(r"\| ([^|]+) - ([^|]+) \|", text)
        extracted_text = self.re.split(r"\| [^|]+ - [^|]+ \|", text)[0].strip() if "|" in text else text.strip()
        return button_data, extracted_text

    def create_keyboard(self, text, inline_cmd=None, is_id=None):
        layout = []
        buttons, remaining_text = self.parse_buttons_and_text(text)

        for label, payload in buttons:
            cb_data, *extra_params = payload.split(";")

            if not self.get_urls(cb_data):
                cb_data = f"{inline_cmd} {is_id}_{cb_data}" if inline_cmd and is_id else cb_data

            button = (
                self.pyrogram.types.InlineKeyboardButton(label, user_id=cb_data)
                if "user" in extra_params
                else (
                    self.pyrogram.types.InlineKeyboardButton(label, url=cb_data) if self.get_urls(cb_data) else self.pyrogram.types.InlineKeyboardButton(label, callback_data=cb_data)
                )
            )

            if "same" in extra_params and layout:
                layout[-1].append(button)
            else:
                layout.append([button])

        return self.pyrogram.types.InlineKeyboardMarkup(layout), remaining_text

    def build_button_grid(self, buttons, row_inline=None, row_width=2):
        row_inline = row_inline or {}

        grid = [[self.pyrogram.types.InlineKeyboardButton(**data) for data in buttons[i : i + row_width]] for i in range(0, len(buttons), row_width)]

        if row_inline:
            grid.append([self.pyrogram.types.InlineKeyboardButton(**row_inline)])

        return self.pyrogram.types.InlineKeyboardMarkup(grid)

    def module(self, page_n, module_dict, same=2, line=5, left_arrow="<<", right_arrow=">>"):
        modules = [self.pyrogram.types.InlineKeyboardButton(x.__MODULE__.lower(), callback_data=f"help_module({x.__MODULE__})") for x in module_dict.keys()]

        pairs = [modules[i : i + same] for i in range(0, len(modules), same)]

        if len(modules) % 1 == 1:
            pairs.append((modules[-1],))

        max_num_pages = self.math.ceil(len(pairs) / line)
        modulo_page = page_n % max_num_pages

        pairs = (
            pairs[modulo_page * line : line * (modulo_page + 1)]
            + [
                (
                    self.pyrogram.types.InlineKeyboardButton(left_arrow, callback_data=f"help_prev({modulo_page})"),
                    self.pyrogram.types.InlineKeyboardButton(right_arrow, callback_data=f"help_next({modulo_page})"),
                )
            ]
            if len(pairs) > line
            else pairs
        )

        return pairs
