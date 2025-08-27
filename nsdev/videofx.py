import asyncio
import functools
import math
import os
import random
import shutil
import subprocess
import tempfile
import urllib.request
from typing import List, Tuple
import shlex

import numpy as np
import requests
from moviepy import VideoClip, VideoFileClip
from PIL import Image, ImageDraw, ImageFont

from .logger import LoggerHandler 

log = LoggerHandler()


class VideoFX:
    def __init__(self):
        self.font_cache_dir = ".cache_fonts"
        os.makedirs(self.font_cache_dir, exist_ok=True)

        try:
            local_fonts = [
                os.path.join(self.font_cache_dir, f)
                for f in os.listdir(self.font_cache_dir)
                if f.lower().endswith(".ttf") and os.path.isfile(os.path.join(self.font_cache_dir, f))
            ]
        except Exception:
            local_fonts = []

        if local_fonts:
            self.available_fonts = local_fonts
        else:
            font_urls = self._fetch_google_font_urls(limit=15)
            self.available_fonts = self._ensure_local_fonts(font_urls)

        random.seed(42)
        self._lightning_phases = [random.random() * 2 * math.pi for _ in range(6)]
        self._lightning_amps = [0.6 + random.random() * 0.8 for _ in range(6)]

    def _fetch_google_font_urls(self, limit: int = 15) -> List[str]:
        all_font_families = []
        base_dirs = ["ofl", "apache"]
        api_base_url = "https://api.github.com/repos/google/fonts/contents/"

        try:
            for dir_name in base_dirs:
                response = requests.get(f"{api_base_url}{dir_name}", timeout=10)
                response.raise_for_status()
                for item in response.json():
                    if isinstance(item, dict) and item.get("type") == "dir":
                        all_font_families.append(item)

            if not all_font_families:
                return []

            random.shuffle(all_font_families)
            selected_families = all_font_families[:limit]
            font_urls = []
            for family in selected_families:
                try:
                    family_response = requests.get(family["url"], timeout=10)
                    family_response.raise_for_status()
                    font_files = family_response.json()
                    if not isinstance(font_files, list):
                        continue
                    regular_match = None
                    any_ttf_match = None
                    for font_file in font_files:
                        if isinstance(font_file, dict) and font_file.get("type") == "file":
                            name = font_file.get("name", "").lower()
                            if "regular" in name and name.endswith(".ttf"):
                                regular_match = font_file
                                break
                            if any_ttf_match is None and name.endswith(".ttf"):
                                any_ttf_match = font_file
                    best_match = regular_match or any_ttf_match
                    if best_match and best_match.get("download_url"):
                        font_urls.append(best_match["download_url"])
                except requests.RequestException:
                    continue
            return font_urls
        except requests.RequestException:
            return []

    def _ensure_local_fonts(self, urls: List[str]) -> List[str]:
        paths: List[str] = []
        for u in urls:
            try:
                name = os.path.basename(u)
                if not name:
                    continue
                local_path = os.path.join(self.font_cache_dir, name)
                if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                    paths.append(local_path)
                    continue
                try:
                    urllib.request.urlretrieve(u, local_path)
                    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                        paths.append(local_path)
                except Exception:
                    if os.path.isfile(local_path) and os.path.getsize(local_path) > 1024:
                        paths.append(local_path)
                    else:
                        continue
            except Exception:
                continue
        return paths

    def _get_font(self, font_size: int):
        if hasattr(self, 'available_fonts') and self.available_fonts:
            random_font_path = random.choice(self.available_fonts)
            try:
                return ImageFont.truetype(random_font_path, font_size)
            except Exception:
                pass
        try:
            return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _compute_lightning_spike(self, t: float, lightning_rate: float, lightning_strength: float) -> float:
        val = 0.0
        for i, phase in enumerate(self._lightning_phases):
            freq = lightning_rate * (1 + i * 0.3)
            amp = self._lightning_amps[i]
            v = abs(math.sin(2 * math.pi * freq * t + phase))
            val += (v**30) * amp
        val = val * lightning_strength
        return max(0.0, min(1.0, val))

    def _bolt_points_around_rect(self, rect, segments=7, jitter=0.25):
        x0, y0, x1, y1 = rect
        w = x1 - x0
        h = y1 - y0
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2
        points = []
        vertical_offset = h * 0.9
        sx = cx + (random.random() - 0.5) * w * 1.2
        sy = cy - vertical_offset
        ex = cx + (random.random() - 0.5) * w * 1.2
        ey = cy + vertical_offset
        for i in range(segments + 1):
            t = i / segments
            x = sx + (ex - sx) * t + (random.random() - 0.5) * w * jitter * (1 - abs(0.5 - t) * 2)
            y = sy + (ey - sy) * t + (random.random() - 0.5) * h * jitter * (1 - abs(0.5 - t) * 2)
            points.append((x, y))
        return points

    def _write_png_sequence_and_encode(self, make_frame, duration: float, fps: int, output_path: str) -> None:
        tmp_dir = tempfile.mkdtemp(prefix="videofx_frames_")
        try:
            nframes = max(1, int(math.ceil(duration * fps)))
            for i in range(nframes):
                t = i / fps
                frame = make_frame(t)
                if frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                img = Image.fromarray(frame)
                img.save(os.path.join(tmp_dir, f"frame_{i:05d}.png"))

            if not output_path.lower().endswith(('.webm', '.mkv')):
                output_path = os.path.splitext(output_path)[0] + '.webm'

            cmd = [
                'ffmpeg', '-y', '-framerate', str(fps), '-i', os.path.join(tmp_dir, 'frame_%05d.png'),
                '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-crf', '30', '-b:v', '0', output_path
            ]
            subprocess.run(cmd, check=True)
        finally:
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass

    def _create_rgb_video(
        self,
        text_lines: List[str],
        output_path: str,
        duration: float,
        fps: int,
        *,
        blink: bool = False,
        blink_rate: float = 2.0,
        blink_duty: float = 0.15,
        blink_smooth: bool = False,
        font_size: int = 90,
        lightning: bool = False,
        lightning_rate: float = 1.0,
        lightning_bolts: int = 2,
        lightning_color: Tuple[int, int, int] = (255, 240, 200),
        lightning_width: int = 2,
        lightning_glow: bool = True,
        lightning_glow_width: int = 10,
        lightning_strength: float = 1.0,
        transparent: bool = True,
    ):
        text_lines = [t.strip() for t in text_lines if t and t.strip()]
        if not text_lines:
            text_lines = [" "]
        font = self._get_font(font_size)
        mode = "RGBA" if transparent else "RGB"
        dummy_img = Image.new(mode, (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        text_widths = [dummy_draw.textbbox((0, 0), line, font=font)[2] for line in text_lines]
        text_heights = [dummy_draw.textbbox((0, 0), line, font=font)[3] for line in text_lines]

        base_w = max(max(text_widths) + 40, 512)
        canvas_w = base_w - (base_w % 2)

        total_h = sum(text_heights) + (len(text_lines) * 20)
        base_h = max(total_h, 512)
        canvas_h = base_h - (base_h % 2)

        if blink and blink_rate > 0:
            period = 1.0 / blink_rate
            on_duration = max(0.0, min(1.0, blink_duty)) * period
        else:
            period = None
            on_duration = None

        def make_frame(t):
            base = Image.new(mode, (canvas_w, canvas_h), (0, 0, 0, 0) if transparent else (0, 0, 0, 255))
            draw_base = ImageDraw.Draw(base)
            r = int(127 * (1 + math.sin(t * 5 + 0))) + 64
            g = int(127 * (1 + math.sin(t * 5 + 2))) + 64
            b = int(127 * (1 + math.sin(t * 5 + 4))) + 64
            intensity = 1.0
            if blink and period is not None:
                if blink_smooth:
                    intensity = 0.5 * (1 + math.sin(2 * math.pi * blink_rate * t - math.pi / 2))
                    intensity = max(0.0, min(1.0, intensity))
                else:
                    phase = t % period
                    intensity = 1.0 if phase < on_duration else 0.0
            rr = int(r * intensity)
            gg = int(g * intensity)
            bb = int(b * intensity)
            current_y = (canvas_h - total_h) / 2
            rects = []
            for i, line in enumerate(text_lines):
                line_w = text_widths[i]
                line_h = text_heights[i]
                position = ((canvas_w - line_w) / 2, current_y)
                if transparent:
                    draw_base.text(position, line, font=font, fill=(rr, gg, bb, 255))
                else:
                    draw_base.text(position, line, font=font, fill=(rr, gg, bb))
                rect_margin = 12 + int(font_size * 0.12)
                x0 = position[0] - rect_margin
                y0 = position[1] - rect_margin
                x1 = position[0] + line_w + rect_margin
                y1 = position[1] + line_h + rect_margin
                rects.append((x0, y0, x1, y1))
                current_y += line_h + 20

            if lightning:
                spike = self._compute_lightning_spike(t, lightning_rate, lightning_strength)
                if spike > 0.003 and rects:
                    overlay = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
                    draw_ov = ImageDraw.Draw(overlay)
                    bolts = max(1, int(lightning_bolts + spike * 4))
                    for bidx in range(bolts):
                        target_rect = random.choice(rects)
                        points = self._bolt_points_around_rect(target_rect, segments=6, jitter=0.28 + spike * 0.5)
                        color_alpha = int(200 * spike)
                        lw = max(1, int(lightning_width * (1 + spike * 3)))
                        col = (lightning_color[0], lightning_color[1], lightning_color[2], color_alpha)
                        if lightning_glow:
                            glow_w = lightning_glow_width + int(spike * 20)
                            for gw in range(glow_w, 0, -3):
                                aal = int(max(8, color_alpha * (gw / (glow_w + 1)) * 0.6))
                                draw_ov.line(points, fill=(lightning_color[0], lightning_color[1], lightning_color[2], aal), width=gw)
                        draw_ov.line(points, fill=col, width=lw)
                    base = Image.alpha_composite(base.convert("RGBA"), overlay).convert(mode)

            arr = np.array(base, dtype=np.uint8)
            if transparent and arr.ndim == 3 and arr.shape[2] == 3:
                alpha = np.full((arr.shape[0], arr.shape[1], 1), 255, dtype=np.uint8)
                arr = np.concatenate([arr, alpha], axis=2)
            return arr

        animation = VideoClip(make_frame, duration=duration)

        if transparent and not output_path.lower().endswith(('.webm', '.mkv')):
            output_path = os.path.splitext(output_path)[0] + '.webm'

        try:
            if transparent:
                animation.write_videofile(
                    output_path,
                    fps=fps,
                    codec="libvpx-vp9",
                    logger=None,
                    ffmpeg_params=["-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0"],
                )
            else:
                animation.write_videofile(
                    output_path,
                    fps=fps,
                    codec="libx264",
                    logger=None,
                    ffmpeg_params=["-pix_fmt", "yuv420p"],
                )
        except Exception as e:
            log.print(f"{log.YELLOW}MoviePy writer failed, falling back to PNG->ffmpeg. Error: {log.RED}{e}")
            if transparent:
                try:
                    self._write_png_sequence_and_encode(make_frame, duration, fps, output_path)
                except Exception as e2:
                    log.print(f"{log.YELLOW}Fallback PNG->ffmpeg juga gagal: {log.RED}{e2}")
                    raise Exception(e2)
            else:
                raise Exception("Ffmpeg callback_query-> error")
        finally:
            animation.close()

    async def text_to_video(
        self,
        text: str,
        output_path: str,
        duration: float = 3.0,
        fps: int = 24,
        *,
        blink: bool = False,
        blink_rate: float = 2.0,
        blink_duty: float = 0.15,
        blink_smooth: bool = False,
        font_size: int = 90,
        lightning: bool = False,
        lightning_rate: float = 1.0,
        lightning_bolts: int = 2,
        lightning_color: Tuple[int, int, int] = (255, 240, 200),
        lightning_width: int = 2,
        lightning_glow: bool = True,
        lightning_glow_width: int = 10,
        lightning_strength: float = 1.0,
        transparent: bool = True,
    ):
        if ";" in text:
            text_lines = text.split(";")
        else:
            text_lines = text.splitlines()
        return await self._run_in_executor(
            self._create_rgb_video,
            text_lines,
            output_path,
            duration,
            fps,
            blink=blink,
            blink_rate=blink_rate,
            blink_duty=blink_duty,
            blink_smooth=blink_smooth,
            font_size=font_size,
            lightning=lightning,
            lightning_rate=lightning_rate,
            lightning_bolts=lightning_bolts,
            lightning_color=lightning_color,
            lightning_width=lightning_width,
            lightning_glow=lightning_glow,
            lightning_glow_width=lightning_glow_width,
            lightning_strength=lightning_strength,
            transparent=transparent,
        )

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30, transparent: bool = True):
        clip = VideoFileClip(video_path)
        max_duration = min(clip.duration, 2.95)
        trimmed_clip = clip.subclip(0, max_duration)
        if trimmed_clip.w >= trimmed_clip.h:
            resized_clip = trimmed_clip.resize(width=512)
        else:
            resized_clip = trimmed_clip.resize(height=512)
        final_clip = resized_clip.set_fps(fps)

        if transparent and not output_path.lower().endswith(('.webm', '.mkv')):
            output_path = os.path.splitext(output_path)[0] + '.webm'

        try:
            if transparent:
                final_clip.write_videofile(
                    output_path,
                    codec='libvpx-vp9',
                    audio=False,
                    logger=None,
                    ffmpeg_params=['-pix_fmt', 'yuva420p', '-crf', '30', '-b:v', '0'],
                )
            else:
                final_clip.write_videofile(
                    output_path,
                    codec='libx264',
                    audio=False,
                    logger=None,
                    ffmpeg_params=['-pix_fmt', 'yuv420p'],
                )
        except Exception as e:
            log.print(f"{log.YELLOW}Sticker write failed, falling back to ffmpeg frames. Error: {log.RED}{e}")
            tmp_dir = tempfile.mkdtemp(prefix='sticker_frames_')
            try:
                nframes = max(1, int(math.ceil(max_duration * fps)))
                for i in range(nframes):
                    t = i / fps
                    frame = final_clip.get_frame(t)
                    if frame.dtype != np.uint8:
                        frame = frame.astype(np.uint8)
                    img = Image.fromarray(frame)
                    img.save(os.path.join(tmp_dir, f"frame_{i:05d}.png"))

                cmd = [
                    'ffmpeg', '-y', '-framerate', str(fps), '-i', os.path.join(tmp_dir, 'frame_%05d.png'),
                    '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-crf', '30', '-b:v', '0', output_path
                ]
                subprocess.run(cmd, check=True)
            finally:
                try:
                    shutil.rmtree(tmp_dir)
                except Exception:
                    pass
        finally:
            clip.close()
            try:
                trimmed_clip.close()
                resized_clip.close()
                final_clip.close()
            except Exception:
                pass

    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30, transparent: bool = True):
        return await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps, transparent)
