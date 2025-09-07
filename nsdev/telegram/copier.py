import asyncio
import os
import re
from typing import Tuple

from pyrogram.raw import functions, types
from pyrogram.errors import FloodWait, RPCError
from pyrogram.types import Message

from ..utils.logger import LoggerHandler
from ..utils.progress import TelegramProgressBar


class MessageCopier:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()
        self._peer_cache = {}

    def _parse_link(self, link: str) -> Tuple[int, int] or Tuple[None, None]:
        public_match = re.match(r"https://t\.me/(\w+)/(\d+)", link)
        if public_match:
            username, msg_id = public_match.groups()
            return username, int(msg_id)

        private_match = re.match(r"https://t\.me/c/(\d+)/(\d+)", link)
        if private_match:
            chat_id_str, msg_id = private_match.groups()
            chat_id = int(f"-100{chat_id_str}")
            return chat_id, int(msg_id)

        return None, None

    async def _get_peer_from_cache_or_api(self, chat_id):
        if chat_id in self._peer_cache:
            return self._peer_cache[chat_id]
        
        peer = await self._client.resolve_peer(chat_id)
        self._peer_cache[chat_id] = peer
        return peer

    async def _get_and_verify_message(self, chat_id, msg_id):
        peer = await self._get_peer_from_cache_or_api(chat_id)

        if isinstance(peer, types.InputPeerChannel):
            raw_result = await self._client.invoke(
                functions.channels.GetMessages(
                    channel=types.InputChannel(channel_id=peer.channel_id, access_hash=peer.access_hash),
                    id=[types.InputMessageID(id=msg_id)]
                )
            )
            if not raw_result.messages:
                raise RPCError(f"Pesan dengan ID {msg_id} tidak ditemukan di channel.")
            
            return await Message._parse(self._client, raw_result.messages[0], {u.id: u for u in raw_result.users}, {c.id: c for c in raw_result.chats})
        else:
            return await self._client.get_messages(chat_id, msg_id)


    async def _process_single_message(self, message: Message, user_chat_id: int, status_message: Message):
        thumb_path = None
        file_path = None
        try:
            if message.media:
                download_progress = TelegramProgressBar(self._client, status_message, task_name="Downloads")
                file_path = await self._client.download_media(message, progress=download_progress.update)
                media_obj = message.video or message.audio
                if media_obj and hasattr(media_obj, "thumbs") and media_obj.thumbs:
                    thumb_path = await self._client.download_media(media_obj.thumbs[-1].file_id)

                upload_progress = TelegramProgressBar(self._client, status_message, task_name="Uploading")
                sender_map = {
                    "video": self._client.send_video, "audio": self._client.send_audio,
                    "document": self._client.send_document, "photo": self._client.send_photo,
                    "voice": self._client.send_voice, "animation": self._client.send_animation,
                    "sticker": self._client.send_sticker,
                }
                if message.media.value in sender_map:
                    send_func = sender_map[message.media.value]
                    kwargs = {"chat_id": user_chat_id, "caption": (message.caption or ""), "progress": upload_progress.update}
                    media_attr = getattr(message, message.media.value, None)
                    if hasattr(media_attr, "duration"): kwargs["duration"] = media_attr.duration
                    if thumb_path: kwargs["thumb"] = thumb_path
                    kwargs[message.media.value] = file_path
                    await send_func(**kwargs)
                else: await message.copy(user_chat_id)
            else: await message.copy(user_chat_id)
        finally:
            if file_path and os.path.exists(file_path): os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path): os.remove(thumb_path)
    
    async def copy_from_links(self, user_chat_id: int, links_text: str, status_message: Message):
        links_to_process = []
        if "|" in links_text:
            parts = [part.strip() for part in links_text.split("|")]
            if len(parts) != 2: raise ValueError("Format rentang tidak valid.")
            chat_id1, msg_id1 = self._parse_link(parts[0])
            chat_id2, msg_id2 = self._parse_link(parts[1])
            if not (chat_id1 and chat_id2) or chat_id1 != chat_id2: raise ValueError("Link tidak valid atau bukan dari chat yang sama.")
            for msg_id in range(min(msg_id1, msg_id2), max(msg_id1, msg_id2) + 1): links_to_process.append((chat_id1, msg_id))
        else:
            for link in links_text.split():
                chat_id, msg_id = self._parse_link(link)
                if chat_id: links_to_process.append((chat_id, msg_id))
        
        if not links_to_process: raise ValueError("Tidak ada link valid yang ditemukan.")
            
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
                self._log.print(f"{self._log.YELLOW}Terkena FloodWait. Menunggu {wait_time} detik...{self._log.RESET}")
                await asyncio.sleep(wait_time)
            except Exception as e:
                self._log.error(f"Gagal memproses link ({chat_id}/{msg_id}): {e}")

        await status_message.edit("✅ **Semua proses selesai!**")
        await asyncio.sleep(3)
        await status_message.delete()
