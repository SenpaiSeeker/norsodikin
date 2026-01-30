from io import BytesIO

from PIL import Image, ImageDraw
from pygments import highlight
from pygments.formatters import ImageFormatter
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.styles import get_all_styles


class CodeRenderer:
    def __init__(self):
        self.default_style = "monokai"

    def get_available_styles(self):
        return list(get_all_styles())

    def render(self, code: str, language: str = None, theme: str = "monokai", line_numbers: bool = True) -> BytesIO:
        try:
            if language:
                lexer = get_lexer_by_name(language, stripall=True)
            else:
                lexer = guess_lexer(code)
        except Exception:
            lexer = get_lexer_by_name("text", stripall=True)

        formatter_opts = {
            "style": theme if theme in self.get_available_styles() else self.default_style,
            "line_numbers": line_numbers,
            "font_size": 24,
            "font_name": "DejaVu Sans Mono",
            "image_pad": 30,
            "line_number_bg": "#202020",
            "line_number_fg": "#aaaaaa",
        }

        image_data = highlight(code, lexer, ImageFormatter(**formatter_opts))

        code_image = Image.open(BytesIO(image_data))

        bg_color = (40, 44, 52)
        padding = 50
        title_bar_height = 60

        final_width = code_image.width + (padding * 2)
        final_height = code_image.height + padding + title_bar_height

        canvas = Image.new("RGB", (final_width, final_height), bg_color)
        draw = ImageDraw.Draw(canvas)

        button_y = padding // 2 + 10
        button_spacing = 30
        start_x = padding

        draw.ellipse((start_x, button_y, start_x + 20, button_y + 20), fill="#ff5f56")
        draw.ellipse((start_x + button_spacing, button_y, start_x + button_spacing + 20, button_y + 20), fill="#ffbd2e")
        draw.ellipse(
            (start_x + button_spacing * 2, button_y, start_x + button_spacing * 2 + 20, button_y + 20), fill="#27c93f"
        )

        canvas.paste(code_image, (padding, title_bar_height))

        output = BytesIO()
        canvas.save(output, format="PNG")
        output.seek(0)

        return output
