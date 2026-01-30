import asyncio
import colorsys
import io
import zipfile

from PIL import Image


class ThemeGenerator:
    def _rgb_to_hex(self, rgb):
        return "{:02x}{:02x}{:02x}".format(*rgb)

    def _hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def _adjust_brightness(self, rgb, factor):
        r, g, b = rgb
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        l = max(min(l * factor, 1.0), 0.0)
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return int(r * 255), int(g * 255), int(b * 255)

    def _get_dominant_color(self, img):
        img = img.resize((150, 150))
        img = img.convert("RGB")
        result = img.quantize(colors=1)
        palette = result.getpalette()[:3]
        return tuple(palette)

    def _is_dark(self, rgb):
        return (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) < 128

    def _generate_theme_content(self, main_rgb):
        is_dark = self._is_dark(main_rgb)

        bg_color = self._rgb_to_hex(main_rgb)
        accent = "50a8eb" if is_dark else "2ea6ff"
        text_primary = "ffffff" if is_dark else "000000"
        text_secondary = "808080"

        darker_bg = self._rgb_to_hex(self._adjust_brightness(main_rgb, 0.8))
        self._rgb_to_hex(self._adjust_brightness(main_rgb, 1.2))

        bubble_in = self._rgb_to_hex(self._adjust_brightness(main_rgb, 1.3)) if is_dark else "ffffff"
        bubble_out = self._rgb_to_hex(self._adjust_brightness(main_rgb, 1.5)) if is_dark else "eeffde"

        template = f"""
windowBackgroundWhite=#{bg_color}
windowBackgroundWhiteBlackText=#{text_primary}
windowBackgroundWhiteGrayText=#{text_secondary}
windowBackgroundWhiteBlueHeader=#{accent}
windowBackgroundWhiteLinkText=#{accent}
windowBackgroundWhiteBlueText=#{accent}

actionBarDefault=#{darker_bg}
actionBarDefaultIcon=#{text_primary}
actionBarDefaultTitle=#{text_primary}
actionBarDefaultSelector=#00000010

chat_inBubble=#{bubble_in}
chat_outBubble=#{bubble_out}
chat_messageText=#{text_primary}
chat_outMessageText=#{text_primary}

listSelectorJDK=#00000010
divider=#{darker_bg}
        """
        return template.strip()

    def _sync_create_theme(self, image_bytes: bytes, output_path: str):
        img = Image.open(io.BytesIO(image_bytes))
        dominant = self._get_dominant_color(img)
        theme_config = self._generate_theme_content(dominant)

        wallpaper_buffer = io.BytesIO()
        img.convert("RGB").save(wallpaper_buffer, format="JPEG", quality=90)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("colors.attheme", theme_config)
            zf.writestr("wallpaper.jpg", wallpaper_buffer.getvalue())

        return output_path

    async def generate_from_image(self, image_bytes: bytes, output_path: str = "custom.attheme") -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_create_theme, image_bytes, output_path)
