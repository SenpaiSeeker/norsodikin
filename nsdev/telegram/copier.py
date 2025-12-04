import asyncio
import os
import re
from typing import List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import pyrogram
from pyrogram.enums import MessagesFilter
from pyrogram.errors import ChatForwardsRestricted, FloodWait, RPCError
from pyrogram.types import InputMediaPhoto, InputMediaVideo, Message

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
                    raise RPCError(f"Gagal akses chat {chat_id}: {e}")

        return await self._client.get_messages(chat_id, msg_id)

    async def _process_single_message(
        self,
        message: Message,
        user_chat_id: int,
        status_message: Message,
        custom_thumb_path: str = None,
        **extra_params,
    ):
        file_path = None
        original_thumb_path = None

        try:
            return await message.copy(user_chat_id, **extra_params)
        except ChatForwardsRestricted:
            await status_message.edit(f"🔒 Konten Terproteksi ({message.id}). Mengunduh manual...")
        except Exception as e:
            await status_message.edit(f"❌ Gagal menyalin langsung ({e}). Mencoba mengunduh...")

        try:
            if not message.media:
                if message.text:
                    return await self._client.send_message(user_chat_id, message.text.html, **extra_params)

            dl_prog = TelegramProgressBar(self._client, status_message, "Downloading Restricted")
            file_path = await self._client.download_media(message, progress=dl_prog.update)

            if not file_path or not os.path.exists(file_path):
                raise ValueError("Gagal mengunduh media terproteksi.")

            media_obj = getattr(message, message.media.value, None)
            thumb_to_use = custom_thumb_path

            if not thumb_to_use and media_obj and getattr(media_obj, "thumbs", None):
                try:
                    original_thumb_path = await self._client.download_media(media_obj.thumbs[-1].file_id)
                    thumb_to_use = original_thumb_path
                except Exception:
                    pass

            upl_prog = TelegramProgressBar(self._client, status_message, "Uploading Restricted")
            
            send_func_name = f"send_{message.media.value}"
            if not hasattr(self._client, send_func_name):
                return 

            send_func = getattr(self._client, send_func_name)
            
            caption = message.caption.html if message.caption else ""
            
            kwargs = {
                "chat_id": user_chat_id,
                "caption": caption,
                "progress": upl_prog.update,
                message.media.value: file_path,
                **extra_params
            }
            
            if hasattr(media_obj, "duration"):
                kwargs["duration"] = media_obj.duration
            if thumb_to_use and message.media.value in ["video", "audio", "document"]:
                kwargs["thumb"] = thumb_to_use

            await send_func(**kwargs)

        except Exception as e:
            self._log.error(f"Gagal process manual: {e}")
        finally:
            for p in [file_path, original_thumb_path]:
                if p and os.path.exists(p):
                    os.remove(p)

    async def copy_from_links(
        self,
        user_chat_id: int,
        links_text: str,
        status_message: Message,
        custom_thumb_message_id: int = None,
        **extra_params,
    ):
        custom_thumb_path = None
        if custom_thumb_message_id:
            await status_message.edit("📥 Mengunduh thumbnail kustom...")
            thumb_msg = await self._client.get_messages(user_chat_id, custom_thumb_message_id)
            if thumb_msg.photo:
                custom_thumb_path = await self._client.download_media(thumb_msg)
            else:
                await status_message.edit("Thumbnail invalid, dilewati.")

        try:
            lower_args = links_text.lower()
            if "--photo" in lower_args or "--video" in lower_args:
                parts = links_text.split()
                target_arg = parts[0]
                limit = 20
                media_type_filter = None
                
                if len(parts) >= 2 and parts[1].isdigit():
                    limit = int(parts[1])
                
                if "--photo" in lower_args:
                    media_type_filter = "photo"
                elif "--video" in lower_args:
                    media_type_filter = "video"

                return await self.copy_mass_media(
                    user_chat_id, 
                    target_arg, 
                    limit, 
                    media_type_filter, 
                    status_message, 
                    **extra_params
                )

            links_to_process = []
            if "|" in links_text:
                raw_parts = [p.strip() for p in links_text.split("|")]
                if len(raw_parts) == 2:
                    cid1, mid1 = self._parse_link(raw_parts[0])
                    cid2, mid2 = self._parse_link(raw_parts[1])
                    if cid1 and cid2 and cid1 == cid2:
                        start, end = sorted([mid1, mid2])
                        links_to_process = [(cid1, i) for i in range(start, end + 1)]
            else:
                for link in links_text.split():
                    c, m = self._parse_link(link)
                    if c and m:
                        links_to_process.append((c, m))

            if not links_to_process:
                raise ValueError("Tidak ada link valid yang ditemukan (atau format perintah mass copy salah).")

            total = len(links_to_process)
            for i, (cid, mid) in enumerate(links_to_process):
                await status_message.edit(f"Menyalin {i+1}/{total}...")
                try:
                    msg = await self._get_and_verify_message(cid, mid)
                    if msg:
                        await self._process_single_message(
                            msg, user_chat_id, status_message, custom_thumb_path, **extra_params
                        )
                    await asyncio.sleep(2)
                except FloodWait as fw:
                    await asyncio.sleep(fw.value + 5)
                    msg = await self._get_and_verify_message(cid, mid)
                    if msg:
                        await self._process_single_message(
                            msg, user_chat_id, status_message, custom_thumb_path, **extra_params
                        )
                except Exception:
                    pass

            await status_message.edit("✅ Selesai.")
            await asyncio.sleep(3)
            await status_message.delete()

        finally:
            if custom_thumb_path and os.path.exists(custom_thumb_path):
                os.remove(custom_thumb_path)

    async def copy_mass_media(
        self,
        dest_chat_id: int,
        target_source: Union[str, int],
        limit: int,
        filter_type: str,
        status_message: Message,
        **kwargs
    ):
        collected_files = []
        thumb_files = []

        try:
            chat = await self._client.get_chat(target_source)
            chat_id = chat.id
        except Exception:
            clean_id = str(target_source)
            if clean_id.startswith("100") and clean_id.isdigit() and len(clean_id) > 10:
                clean_id = f"-{clean_id}"
            
            if clean_id.lstrip("-").isdigit():
                chat_id = int(clean_id)
            else:
                chat_id = target_source

        try:
             await self._client.resolve_peer(chat_id)
        except Exception as e:
             raise ValueError(f"Tidak dapat mengakses chat {chat_id}. Pastikan Userbot sudah join.\nError: {e}")

        pyro_filter = MessagesFilter.PHOTO if filter_type == "photo" else MessagesFilter.VIDEO

        await status_message.edit(f"📥 Mengunduh {limit} {filter_type} dari {chat_id}...")

        processed = 0
        progress = TelegramProgressBar(self._client, status_message)
        
        async for msg in self._client.search_messages(chat_id, limit=limit, filter=pyro_filter):
            file_path = None
            thumb_path = None
            caption = msg.caption.html if msg.caption else ""

            try:
                if filter_type == "photo":
                    progress.reset(new_task_name=f"Downloading Photo {processed + 1}")
                    file_path = await self._client.download_media(msg, progress=progress.update)
                    if file_path:
                        collected_files.append(
                            InputMediaPhoto(file_path, caption=caption)
                        )
                        processed += 1

                elif filter_type == "video":
                    progress.reset(new_task_name=f"Downloading Video {processed + 1}")
                    file_path = await self._client.download_media(msg, progress=progress.update)
                    
                    if msg.video.thumbs:
                        try:
                            thumb_path = await self._client.download_media(msg.video.thumbs[-1].file_id)
                            thumb_files.append(thumb_path)
                        except Exception:
                            pass

                    if file_path:
                        collected_files.append(
                            InputMediaVideo(
                                media=file_path, 
                                caption=caption,
                                duration=msg.video.duration or 0,
                                thumb=thumb_path
                            )
                        )
                        processed += 1
                
                if len(collected_files) >= 9:
                    await self._client.send_media_group(dest_chat_id, collected_files, **kwargs)
                    
                    for item in collected_files:
                        if os.path.exists(item.media):
                            os.remove(item.media)
                    for t_path in thumb_files:
                        if t_path and os.path.exists(t_path):
                            os.remove(t_path)
                    
                    collected_files = []
                    thumb_files = []
                    await asyncio.sleep(4)

            except FloodWait as fw:
                await asyncio.sleep(fw.value + 3)
            except Exception as e:
                self._log.error(f"Error processing mass media: {e}")

        if collected_files:
            try:
                await self._client.send_media_group(dest_chat_id, collected_files, **kwargs)
            except Exception as e:
                self._log.error(f"Error sending final batch: {e}")
            finally:
                for item in collected_files:
                    if os.path.exists(item.media):
                        os.remove(item.media)
                for t_path in thumb_files:
                    if t_path and os.path.exists(t_path):
                        os.remove(t_path)

        await status_message.edit(f"✅ Proses salin massal selesai. Total {processed} file terkirim.")
        await asyncio.sleep(3)
        await status_message.delete()
