import asyncio
import os
import re
from typing import Tuple

from pyrogram.errors import RPCError
from pyrogram.types import Message

from ..utils.progress import TelegramProgressBar


class MessageCopier:
    def __init__(self, client):
        self._client = client

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

    async def _process_single_message(self, message: Message, user_chat_id: int, status_message: Message):
        thumb_path = None
        file_path = None

        try:
            if message.media:
                download_progress = TelegramProgressBar(self._client, status_message, task_name="Downloads")
                file_path = await self._client.download_media(
                    message,
                    progress=download_progress.update
                )

                media_obj = message.video or message.audio
                if media_obj and hasattr(media_obj, "thumbs") and media_obj.thumbs:
                    thumb_path = await self._client.download_media(media_obj.thumbs[-1].file_id)

                upload_progress = TelegramProgressBar(self._client, status_message, task_name="Uploading")
                media_type = message.media.value
                
                sender_map = {
                    "video": self._client.send_video,
                    "audio": self._client.send_audio,
                    "document": self._client.send_document,
                    "photo": self._client.send_photo,
                    "voice": self._client.send_voice,
                    "animation": self._client.send_animation,
                    "sticker": self._client.send_sticker
                }

                if media_type in sender_map:
                    send_func = sender_map[media_type]
                    
                    kwargs = {
                        "chat_id": user_chat_id,
                        media_type: file_path,
                        "caption": message.caption.html if message.caption else "",
                        "progress": upload_progress.update,
                    }

                    media_attributes = getattr(message, media_type, None)
                    if media_attributes:
                        if hasattr(media_attributes, "duration") and media_attributes.duration:
                            kwargs["duration"] = media_attributes.duration
                        
                        if thumb_path and media_type in ["video", "audio"]:
                            kwargs["thumb"] = thumb_path
                    
                    await send_func(**kwargs)
                else:
                    await message.copy(user_chat_id)
            else:
                await message.copy(user_chat_id)
        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)

    async def copy_from_links(self, user_chat_id: int, links_text: str, status_message: Message):
        if "|" in links_text:
            parts = [part.strip() for part in links_text.split("|")]
            if len(parts) != 2:
                raise ValueError("Format rentang tidak valid. Gunakan: `link_awal | link_akhir`")
            
            chat_id1, msg_id1 = self._parse_link(parts[0])
            chat_id2, msg_id2 = self._parse_link(parts[1])

            if not (chat_id1 and chat_id2) or chat_id1 != chat_id2:
                raise ValueError("Link tidak valid atau tidak berasal dari chat yang sama untuk rentang.")
            
            start_id = min(msg_id1, msg_id2)
            end_id = max(msg_id1, msg_id2)
            message_ids = list(range(start_id, end_id + 1))
            chat_id_to_process = chat_id1

            await status_message.edit(f"Siap menyalin {len(message_ids)} pesan dari {chat_id_to_process}...")
            await asyncio.sleep(2)
            
            total = len(message_ids)
            for i, msg_id in enumerate(message_ids):
                await status_message.edit(f"Memproses pesan {i+1}/{total} (ID: {msg_id})...")
                try:
                    message = await self._client.get_messages(chat_id_to_process, msg_id)
                    if message.empty:
                        continue
                    await self._process_single_message(message, user_chat_id, status_message)
                    await asyncio.sleep(1)
                except RPCError as e:
                    await self._client.send_message(user_chat_id, f"Gagal mengambil pesan ID {msg_id}: {e}")
                except Exception as e:
                    await self._client.send_message(user_chat_id, f"Terjadi kesalahan pada pesan ID {msg_id}: {e}")

        else:
            links = links_text.split()
            total = len(links)
            for i, link in enumerate(links):
                chat_id, msg_id = self._parse_link(link)
                if not chat_id:
                    await self._client.send_message(user_chat_id, f"Link tidak valid: {link}")
                    continue
                
                await status_message.edit(f"Memproses link {i+1}/{total}...")
                try:
                    message = await self._client.get_messages(chat_id, msg_id)
                    if message.empty:
                        await self._client.send_message(user_chat_id, f"Pesan di link ini kosong atau telah dihapus:\n`{link}`")
                        continue
                    await self._process_single_message(message, user_chat_id, status_message)
                    await asyncio.sleep(1)
                except RPCError as e:
                    await self._client.send_message(user_chat_id, f"Gagal mengambil pesan dari link `{link}`: `{e}`")
                except Exception as e:
                     await self._client.send_message(user_chat_id, f"Terjadi kesalahan pada link `{link}`: `{e}`")

        await status_message.edit("✅ Semua proses selesai!")
        await asyncio.sleep(3)
        await status_message.delete()
