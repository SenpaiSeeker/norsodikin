import asyncio
import functools
import gzip
import json
import os
import random
import subprocess
from typing import List

from lottie.exporters.core import export_tgs
from lottie.objects import Animation, assets, layers, aind, shapes
from lottie.utils.font import Font
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from ..utils.font_manager import FontManager


class VideoFX(FontManager):
    def __init__(self):
        super().__init__()

    async def _run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        call = functools.partial(func, *args, **kwargs)
        return await loop.run_in_executor(None, call)

    def _create_lottie_animation(self, text_lines: List[str], font_size: int):
        font_path = self._get_font_from_package("NotoSans-Bold.ttf", font_size).path
        font_name = os.path.basename(font_path).split('.')[0]
        
        anim = Animation(60)
        anim.op = 180
        font_asset = Font(font_path)
        font_asset.name = font_name
        anim.fonts.add(font_asset)

        y_offset = 0
        max_width = 0
        
        for i, line in enumerate(text_lines):
            fill_color = shapes.Fill(
                aind.ColorKeyframe(0, aind.Vector(random.random(), random.random(), random.random())),
                aind.ColorKeyframe(60, aind.Vector(random.random(), random.random(), random.random())),
            )

            text_shape = shapes.Text(line, font_name=font_name, size=font_size)
            text_layer_shape = shapes.Group(
                [text_shape],
                transform=aind.Transform(position=aind.Vector(0, y_offset))
            )
            text_width = text_shape.font_size * len(line) * 0.6
            if text_width > max_width:
                max_width = text_width
            
            y_offset += font_size * 1.2
            
            shape_layer = layers.ShapeLayer()
            shape_layer.add_shape(text_layer_shape)
            shape_layer.add_shape(fill_color)
            anim.add_layer(shape_layer)

        for layer in anim.layers:
            layer.transform.position.value.x = (512 - max_width) / 2
            layer.transform.position.value.y = (512 - y_offset) / 2
            
            layer.transform.scale.add_keyframe(0, aind.Vector(0, 0))
            layer.transform.scale.add_keyframe(15, aind.Vector(110, 110))
            layer.transform.scale.add_keyframe(30, aind.Vector(100, 100))
            
            layer.transform.opacity.add_keyframe(0, 0)
            layer.transform.opacity.add_keyframe(10, 100)
            layer.transform.opacity.add_keyframe(170, 100)
            layer.transform.opacity.add_keyframe(180, 0)

        return anim

    async def text_to_tgs(self, text: str, output_path: str, font_size: int = 90):
        text_lines = text.split(";") if ";" in text else text.splitlines()
        
        anim_object = await self._run_in_executor(self._create_lottie_animation, text_lines, font_size)
        
        export_tgs(anim_object, output_path)
        return output_path

    def _sync_create_afk_animation(self, text_lines: List[str], output_path: str):
        font_main = self._get_font_from_package("NotoSans-Bold.ttf", 60)
        font_sub = self._get_font_from_package("NotoSans-Regular.ttf", 40)

        canvas_w, canvas_h = 512, 288
        img = Image.new("RGB", (canvas_w, canvas_h), "#181818")
        draw = ImageDraw.Draw(img)

        y_pos = 60
        for i, line in enumerate(text_lines):
            font = font_main if i == 0 else font_sub
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_h = bbox[3] - bbox[1]
            draw.text(((canvas_w - line_w) / 2, y_pos), line, font=font, fill="#FFFFFF")
            y_pos += line_h + 20

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", "-", "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-c:v", "libx264", "-t", "5", "-pix_fmt", "yuv420p", "-vf", "scale=512:288", "-c:a", "aac", "-shortest",
            output_path,
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        img.save(proc.stdin, "PNG")
        _, stderr = proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during AFK animation creation: {stderr.decode(errors='ignore')}")

    async def create_afk_animation(self, text_lines: List[str], output_path: str):
        await self._run_in_executor(self._sync_create_afk_animation, text_lines, output_path)
        return output_path

    def _convert_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        try:
            ffprobe_cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path,
            ]
            result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError):
            duration = 3.0

        trim_duration = min(duration, 2.95)
        scale_filter = "scale='if(gt(a,1),512,-2)':'if(gt(a,1),-2,512)'"

        ffmpeg_cmd = [
            "ffmpeg", "-y", "-i", video_path, "-t", str(trim_duration), "-vf", f"{scale_filter},fps={fps}",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "30", "-b:v", "0", "-an", output_path,
        ]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during sticker conversion: {result.stderr}")

    async def video_to_sticker(self, video_path: str, output_path: str, fps: int = 30):
        await self._run_in_executor(self._convert_to_sticker, video_path, output_path, fps=fps)
        return output_path

    def _convert_video_to_gif(self, video_path: str, output_path: str):
        vf_filter = "fps=15,scale=512:-1:flags=lanczos"
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf_filter, "-c:v", "gif", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during GIF conversion: {result.stderr}")

    async def video_to_gif(self, video_path: str, output_path: str):
        await self._run_in_executor(self._convert_video_to_gif, video_path, output_path)
        return output_path

    def _add_text_to_video(self, video_path: str, output_path: str, top_text: str, bottom_text: str):
        font = self._get_font(70)

        def escape_ffmpeg_text(text):
            return text.replace("'", "'\\''")

        top_drawtext = f"drawtext=fontfile='{font.path}':text='{escape_ffmpeg_text(top_text.upper())}':fontcolor=white:fontsize=80:borderw=2:bordercolor=black:x=(w-text_w)/2:y=20"
        bottom_drawtext = f"drawtext=fontfile='{font.path}':text='{escape_ffmpeg_text(bottom_text.upper())}':fontcolor=white:fontsize=80:borderw=2:bordercolor=black:x=(w-text_w)/2:y=h-text_h-20"

        filters_list = []
        if top_text:
            filters_list.append(top_drawtext)
        if bottom_text:
            filters_list.append(bottom_drawtext)

        vf_filter = ",".join(filters_list)
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-vf", vf_filter, "-c:a", "copy", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during animated meme creation: {result.stderr}")

    async def add_text_to_video(self, video_path: str, output_path: str, top_text: str = "", bottom_text: str = ""):
        await self._run_in_executor(self._add_text_to_video, video_path, output_path, top_text, bottom_text)
        return output_path

    def _sync_video_to_audio(self, video_path: str, output_path: str):
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-q:a", "0", "-map", "a", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during audio extraction: {result.stderr}")

    async def video_to_audio(self, video_path: str, output_path: str):
        await self._run_in_executor(self._sync_video_to_audio, video_path, output_path)
        return output_path

    def _sync_trim_video(self, video_path: str, output_path: str, start_time: str, end_time: str):
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-ss", start_time, "-to", end_time, "-c", "copy", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during video trim: {result.stderr}")

    async def trim_video(self, video_path: str, output_path: str, start_time: str, end_time: str):
        await self._run_in_executor(self._sync_trim_video, video_path, output_path, start_time, end_time)
        return output_path

    def _sync_change_speed(self, video_path: str, output_path: str, speed_factor: float):
        if speed_factor <= 0:
            raise ValueError("Speed factor must be positive.")
        filter_complex = f"[0:v]setpts={1/speed_factor}*PTS[v];[0:a]atempo={speed_factor}[a]"
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", video_path, "-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]", output_path]
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed during speed change: {result.stderr}")

    async def change_speed(self, video_path: str, output_path: str, speed_factor: float):
        await self._run_in_executor(self._sync_change_speed, video_path, output_path, speed_factor)
        return output_path

    async def split_video(self, video_path: str, output_dir: str, split_duration: int) -> list:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        ffprobe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path,
        ]
        process = await asyncio.create_subprocess_exec(*ffprobe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            raise RuntimeError(f"FFprobe error: {stderr.decode().strip()}")
        try:
            total_duration = float(stdout.decode().strip())
        except ValueError:
            raise ValueError("Could not determine video duration.")

        num_parts = math.ceil(total_duration / split_duration)
        split_files = []
        for i in range(num_parts):
            start_time = i * split_duration
            output_path = os.path.join(output_dir, f"part_{i:03d}.mp4")
            command = [
                "ffmpeg", "-i", video_path, "-ss", str(start_time), "-t", str(split_duration), "-c:v", "libx264",
                "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-y", output_path,
            ]
            process = await asyncio.create_subprocess_exec(*command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            _, stderr = await process.communicate()
            if process.returncode != 0:
                error_message = stderr.decode().strip()
                raise RuntimeError(f"FFmpeg error on part {i}: {error_message}")
            split_files.append(output_path)
        return split_files
