import asyncio
import os
import re

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.raw.types.stories import MessageMediaPhoto as StoriesMessageMediaPhoto
from pyrogram.raw.types.stories import MessageMediaVideo as StoriesMessageMediaVideo
from pyrogram.raw.types.stories import MessageMediaUnsupported as StoriesMessageMediaUnsupported
from pyrogram.types import Message, Photo, Video

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

            if single_story_id:
                stories_result = await self._client.invoke(
                    functions.stories.GetStoriesByID(peer=peer, id=[single_story_id])
                )
                active_stories = stories_result.stories
            else:
                peer_stories = await self._client.invoke(functions.stories.GetPeerStories(peer=peer))
                active_stories = peer_stories.stories.stories

            if not active_stories:
                return await status_message.edit_text(f"✅ Pengguna `{target_user}` tidak memiliki story aktif atau story yang dicari tidak ditemukan.")

            total = len(active_stories)
            await status_message.edit_text(f"✅ Ditemukan {total} story. Memulai pengunduhan & pengiriman...")

            for i, story in enumerate(active_stories):
                if isinstance(story, types.StoryItemSkipped):
                    self._log.print(f"{self._log.YELLOW}Melewati story yang tidak dapat diakses (ID: {story.id}).")
                    continue
                    
                downloaded_path = None
                try:
                    await status_message.edit_text(f"📥 Memproses story {i + 1}/{total}...")

                    high_level_media = None
                    send_method = None
                    caption = story.caption or ""

                    if hasattr(story, 'media') and story.media:
                        if isinstance(story.media, StoriesMessageMediaPhoto) and hasattr(story.media, "photo"):
                            high_level_media = Photo._parse(self._client, story.media.photo)
                            send_method = self._client.send_photo
                        elif isinstance(story.media, StoriesMessageMediaVideo) and hasattr(story.media, "video"):
                            high_level_media = Video._parse(self._client, story.media.video, "video.mp4")
                            send_method = self._client.send_video
                        elif isinstance(story.media, StoriesMessageMediaUnsupported):
                            self._log.print(f"{self._log.YELLOW}Melewati story dengan media yang tidak didukung (ID: {story.id}).")
                            continue

                    if high_level_media and send_method:
                        downloaded_path = await self._client.download_media(high_level_media)
                        await send_method(chat_id, downloaded_path, caption=caption)
                        await asyncio.sleep(1.5)
                    else:
                        self._log.print(f"{self._log.YELLOW}Tidak ada media yang valid untuk diunduh pada story (ID: {story.id}).")

                except Exception as item_e:
                    self._log.print(f"{self._log.YELLOW}Gagal memproses satu story: {item_e}")
                finally:
                    if downloaded_path and os.path.exists(downloaded_path):
                        os.remove(downloaded_path)

            await status_message.edit_text("✅ Semua story telah diproses!")
            await asyncio.sleep(3)
            await status_message.delete()

        except Exception as e:
            self._log.print(f"{self._log.RED}Gagal mengunduh story dari {target_user}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat memproses story: `{e}`")
