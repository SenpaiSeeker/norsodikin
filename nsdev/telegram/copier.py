import asyncio
import os
import re
from typing import Tuple, Union

from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from ..utils.logger import LoggerHandler
from ..utils.progress import TelegramProgressBar


class MessageCopier:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()
        self._peer_cache = {}

    def _parse_link(self, link: str) -> Tuple[Union[str, int], int] or Tuple[None, None]:
        link = link.strip()
        public_match = re.match(r"https?://t\.me/([a-zA-Z0-9_]{5,32})/(\d+)", link)
        if public_match:
            return public_match.group(1), int(public_match.group(2))
        private_match = re.match(r"https?://t\.me/c/(\d+)/(\d+)", link)
        if private_match:
            chat_id_str, msg_id = private_match.groups()
            try:
                return int(f"-100{chat_id_str}"), int(msg_id)
            except ValueError:
                pass
        return None, None

    async def _force_get_peer_for_private_chat(self, chat_id_to_find: int):
        if chat_id_to_find in self._peer_cache:
            return
        try:
            await self._client.resolve_peer(chat_id_to_find)
            self._peer_cache[chat_id_to_find] = True
        except Exception as e:
            raise RPCError(f"Gagal mengakses chat {chat_id_to_find}. Pastikan Anda anggota. Detail: {e}")

    async def _get_and_verify_message(self, chat_id, msg_id):
        if chat_id == "c":
            raise RPCError("Parsing gagal: chat_id tidak valid.")
        if isinstance(chat_id, str) and chat_id.isdigit():
            chat_id = int(chat_id)
        await self._force_get_peer_for_private_chat(chat_id)
        return await self._client.get_messages(chat_id, msg_id)

    async def _process_single_message(self, message: Message, user_chat_id: int, status_message: Message):
        thumb_path = file_path = None
        try:
            if not message.media:
                await message.copy(user_chat_id)
                return

            download_progress = TelegramProgressBar(self._client, status_message, "Downloads")
            file_path = await self._client.download_media(message, progress=download_progress.update)

            media_obj = message.video or message.audio
            if media_obj and getattr(media_obj, "thumbs", None):
                thumb_path = await self._client.download_media(media_obj.thumbs[-1].file_id)

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

            if message.media.value in send_map:
                send_func = send_map[message.media.value]
                kwargs = {
                    "chat_id": user_chat_id,
                    "caption": message.caption or "",
                    "progress": upload_progress.update,
                }
                media_attr = getattr(message, message.media.value)
                if hasattr(media_attr, "duration"):
                    kwargs["duration"] = media_attr.duration
                if thumb_path:
                    kwargs["thumb"] = thumb_path
                kwargs[message.media.value] = file_path
                await send_func(**kwargs)
            else:
                await message.copy(user_chat_id)

        finally:
            for path in [file_path, thumb_path]:
                if path and os.path.exists(path):
                    os.remove(path)

    async def copy_from_links(self, user_chat_id: int, links_text: str, status_message: Message):
        links_to_process = []

        if "|" in links_text:
            parts = [p.strip() for p in links_text.split("|")]
            if len(parts) != 2:
                raise ValueError("Format rentang tidak valid.")
            chat_id1, msg_id1 = self._parse_link(parts[0])
            chat_id2, msg_id2 = self._parse_link(parts[1])
            if not (chat_id1 and chat_id2) or chat_id1 != chat_id2:
                raise ValueError("Link tidak valid atau bukan dari chat yang sama.")
            for msg_id in range(min(msg_id1, msg_id2), max(msg_id1, msg_id2) + 1):
                links_to_process.append((chat_id1, msg_id))
        else:
            for link in links_text.split():
                chat_id, msg_id = self._parse_link(link)
                if chat_id is None:
                    self._log.error(f"Link tidak valid: {link}")
                    continue
                if chat_id == "c":
                    self._log.error(f"Parsing gagal: {link}")
                    continue
                links_to_process.append((chat_id, msg_id))

        if not links_to_process:
            raise ValueError("Tidak ada link valid yang ditemukan.")

        await status_message.edit(f"Siap menyalin {len(links_to_process)} pesan...")
        await asyncio.sleep(2)

        total = len(links_to_process)
        for i, (chat_id, msg_id) in enumerate(links_to_process):
            try:
                await status_message.edit(f"Memproses pesan {i+1}/{total} (ID: {msg_id})...")
                message = await self._get_and_verify_message(chat_id, msg_id)
                if not message.empty:
                    await self._process_single_message(message, user_chat_id, status_message)
                    await asyncio.sleep(1.5)
            except FloodWait as e:
                wait_time = e.value + 2
                self._log.print(f"{self._log.YELLOW}FloodWait: tunggu {wait_time} detik...{self._log.RESET}")
                await asyncio.sleep(wait_time)
            except Exception as e:
                self._log.error(f"Gagal memproses ({chat_id}/{msg_id}): {e}")

        await status_message.edit("✅ **Selesai!**")
        await asyncio.sleep(3)
        await status_message.delete()
