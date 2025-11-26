import asyncio
import os
import re
from typing import Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from ..utils.logger import LoggerHandler
from ..utils.progress import TelegramProgressBar


class MessageCopier:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()
        self._peer_cache = {}

    def _parse_link(self, link: str) -> Tuple[Optional[Union[str, int]], Optional[int]]:
        link = link.strip()

        if link.startswith("tg://openmessage"):
            parsed_url = urlparse(link)
            query_params = parse_qs(parsed_url.query)
            user_id = query_params.get("user_id", [None])[0]
            message_id = query_params.get("message_id", [None])[0]
            if user_id and message_id:
                try:
                    return int(user_id), int(message_id)
                except (ValueError, TypeError):
                    return None, None

        pattern = r"https?://t\.me/(?:c/)?(\w+)/(\d+)(?:/(\d+))?"
        match = re.match(pattern, link)
        if match:
            groups = match.groups()
            chat_id_str = groups[0]
            message_id = int(groups[-1] or groups[-2])

            if chat_id_str.isdigit():
                return int(f"-100{chat_id_str}"), message_id
            else:
                return chat_id_str, message_id

        return None, None

    async def _get_and_verify_message(self, chat_id, msg_id):
        if isinstance(chat_id, str) and chat_id.lstrip("-").isdigit():
            chat_id = int(chat_id)

        if isinstance(chat_id, int) and chat_id < 0:
            if chat_id not in self._peer_cache:
                try:
                    await self._client.resolve_peer(chat_id)
                    self._peer_cache[chat_id] = True
                except Exception as e:
                    raise RPCError(f"Gagal akses chat {chat_id}. Pastikan Anda anggota. Detail: {e}")

        return await self._client.get_messages(chat_id, msg_id)


    async def _process_single_message(
        self, message: Message, user_chat_id: int, status_message: Message, custom_thumb_path: str = None, **extra_params,
    ):
        original_thumb_path = None
        file_path = None

        try:
            download_progress = TelegramProgressBar(self._client, status_message, "Downloading")

            if not message.media:
                return await message.copy(user_chat_id)

            file_path = await self._client.download_media(message, progress=download_progress.update)
            if not file_path or not os.path.exists(file_path):
                return await message.copy(user_chat_id)

            media_obj = getattr(message, message.media.value, None)

            thumb_to_use = None
            if custom_thumb_path:
                thumb_to_use = custom_thumb_path
            elif media_obj and hasattr(media_obj, "thumbs") and media_obj.thumbs:
                try:
                    original_thumb_path = await self._client.download_media(media_obj.thumbs[0].file_id)
                    thumb_to_use = original_thumb_path
                except Exception:
                    pass

            upload_progress = TelegramProgressBar(self._client, status_message, "Uploading")
            send_map = {
                "video": self._client.send_video,
                "audio": self._client.send_audio,
                "document": self._client.send_document,
                "photo": self._client.send_photo,
                "voice": self._client.send_voice,
                "animation": self._client.send_animation,
                "sticker": self._client.send_sticker,
            }

            media_type = message.media.value

            if media_type in send_map:
                send_func = send_map[media_type]
                caption = message.caption.html if hasattr(message.caption, "html") else (message.caption or "")
                kwargs = {
                    "chat_id": user_chat_id,
                    "caption": caption,
                    "progress": upload_progress.update,
                    **extra_params
                }

                kwargs[media_type] = file_path

                if hasattr(media_obj, "duration"):
                    kwargs["duration"] = media_obj.duration

                if thumb_to_use and media_type in ["video", "audio", "document"]:
                    kwargs["thumb"] = thumb_to_use

                await send_func(**kwargs)
            else:
                await message.copy(user_chat_id)

        finally:
            for path in [file_path, original_thumb_path]:
                if path and os.path.exists(path):
                    os.remove(path)
