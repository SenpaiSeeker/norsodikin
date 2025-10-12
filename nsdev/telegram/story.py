import asyncio
import os
import re

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..utils.logger import LoggerHandler


class StoryDownloader:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()
    
    async def _parse_story_link(self, link: str):
        match = re.match(r"https?://t\.me/(\w+)/s/(\d+)", link)
        if match:
            return match.groups()
        return None, None

    async def download_user_stories(self, username_or_link: str, chat_id: int, status_message: Message):
        if self._client.me.is_bot:
            raise Exception("Bot accounts cannot download stories. This feature requires a Userbot.")
            
        target_user = username_or_link
        single_story_id = None
        
        username_from_link, story_id_from_link = await self._parse_story_link(username_or_link)
        if username_from_link and story_id_from_link:
            target_user = username_from_link
            single_story_id = int(story_id_from_link)
            await status_message.edit_text(f"Mengekstrak story dari tautan untuk `{target_user}`...")
        else:
            await status_message.edit_text(f"Mencari pengguna `{target_user}`...")

        try:
            user = await self._client.get_users(target_user)
        except (UsernameInvalid, PeerIdInvalid):
            return await status_message.edit_text(f"❌ Pengguna `{target_user}` tidak ditemukan.")
        except RPCError as e:
            return await status_message.edit_text(f"❌ Gagal mendapatkan info pengguna: `{e}`")

        try:
            peer = await self._client.resolve_peer(user.id)
            
            stories_result = None
            if single_story_id:
                stories_result = await self._client.invoke(
                    functions.stories.GetStoriesByID(peer=peer, id=[single_story_id])
                )
            else:
                stories_result = await self._client.invoke(functions.stories.GetPeerStories(peer=peer))

            active_stories = []
            if stories_result:
                if isinstance(stories_result, types.stories.PeerStories):
                    peer_stories_obj = getattr(stories_result, 'stories', None)
                    if peer_stories_obj:
                        active_stories = getattr(peer_stories_obj, 'stories', []) or []
                elif isinstance(stories_result, types.stories.Stories):
                    active_stories = getattr(stories_result, 'stories', []) or []

            if not active_stories:
                return await status_message.edit_text(f"✅ Pengguna `{target_user}` tidak memiliki story aktif atau story yang dicari tidak ditemukan.")
            
            users = {u.id: u for u in getattr(stories_result, 'users', [])}
            chats = {c.id: c for c in getattr(stories_result, 'chats', [])}

            total = len(active_stories)
            await status_message.edit_text(f"✅ Ditemukan {total} story. Memulai pengunduhan & pengiriman...")

            for i, story in enumerate(active_stories):
                if isinstance(story, types.StoryItemSkipped):
                    self._log.print(f"{self._log.YELLOW}Melewati story yang tidak dapat diakses (ID: {story.id}).")
                    continue
                    
                downloaded_path = None
                try:
                    await status_message.edit_text(f"📥 Memproses story {i + 1}/{total}...")

                    if not hasattr(story, 'media') or not story.media:
                        self._log.print(f"{self._log.YELLOW}Melewati story tanpa media (ID: {story.id}).")
                        continue
                    
                    raw_message = types.Message(
                        id=story.id,
                        peer_id=peer,
                        date=story.date,
                        message=story.caption or "",
                        media=story.media
                    )

                    parsed_message = await Message._parse(
                        self._client, raw_message,
                        users=users,
                        chats=chats
                    )
                    
                    if parsed_message is None:
                        self._log.print(f"{self._log.YELLOW}Gagal mem-parsing story menjadi pesan (ID: {story.id}).")
                        continue

                    media_to_download = None
                    send_method = None
                    caption = parsed_message.caption if parsed_message.caption else ""

                    if parsed_message.photo:
                        media_to_download = parsed_message.photo
                        send_method = self._client.send_photo
                    elif parsed_message.video:
                        media_to_download = parsed_message.video
                        send_method = self._client.send_video
                    else:
                        self._log.print(f"{self._log.YELLOW}Melewati story dengan media yang tidak didukung (ID: {story.id}).")
                        continue
                        
                    if media_to_download and send_method:
                        downloaded_path = await self._client.download_media(media_to_download)
                        await send_method(chat_id, downloaded_path, caption=caption)
                        await asyncio.sleep(1.5)

                except Exception as item_e:
                    self._log.print(f"{self._log.YELLOW}Gagal memproses satu story: {item_e}")
                    self._log.print(f"{self._log.RED}{item_e.__class__.__name__}: {item_e}")

                finally:
                    if downloaded_path and os.path.exists(downloaded_path):
                        os.remove(downloaded_path)

            await status_message.edit_text("✅ Semua story telah diproses!")
            await asyncio.sleep(3)
            await status_message.delete()

        except Exception as e:
            self._log.print(f"{self._log.RED}Gagal mengunduh story dari {target_user}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat memproses story: `{e}`")
