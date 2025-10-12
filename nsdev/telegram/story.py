import asyncio
import os

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message, Photo, Video

from ..utils.logger import LoggerHandler


class StoryDownloader:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()

    async def download_user_stories(self, username: str, chat_id: int, status_message: Message):
        if self._client.me.is_bot:
            raise Exception("Bot accounts cannot download stories. This feature requires a Userbot.")

        try:
            await status_message.edit_text(f"Mencari pengguna `{username}`...")
            user = await self._client.get_users(username)
        except (UsernameInvalid, PeerIdInvalid):
            return await status_message.edit_text(f"❌ Pengguna `{username}` tidak ditemukan.")
        except RPCError as e:
            return await status_message.edit_text(f"❌ Gagal mendapatkan info pengguna: `{e}`")

        try:
            peer = await self._client.resolve_peer(user.id)

            peer_stories = await self._client.invoke(functions.stories.GetPeerStories(peer=peer))

            active_stories = peer_stories.stories.stories

            if not active_stories:
                return await status_message.edit_text(f"✅ Pengguna `{username}` tidak memiliki story aktif.")

            total = len(active_stories)
            await status_message.edit_text(f"✅ Ditemukan {total} story aktif. Memulai pengunduhan & pengiriman...")

            for i, story in enumerate(active_stories):
                downloaded_path = None
                try:
                    if not isinstance(story, types.StoryItem):
                        self._log.print(f"{self._log.YELLOW}Melewatkan story yang tidak dapat diakses (tipe: {type(story).__name__}).")
                        continue

                    await status_message.edit_text(f"📥 Memproses story {i + 1}/{total}...")

                    high_level_media = None
                    send_method = None
                    caption = story.caption or ""

                    if hasattr(story.media, "photo") and isinstance(story.media.photo, types.Photo):
                        high_level_media = Photo._parse(self._client, story.media.photo)
                        send_method = self._client.send_photo
                    elif hasattr(story.media, "video") and isinstance(story.media.video, types.Video):
                        high_level_media = Video._parse(self._client, story.media.video, "video")
                        send_method = self._client.send_video

                    if high_level_media:
                        downloaded_path = await self._client.download_media(high_level_media)
                        await send_method(chat_id, downloaded_path, caption=caption)
                        await asyncio.sleep(1.5)

                except Exception as item_e:
                    self._log.print(f"{self._log.YELLOW}Gagal memproses satu story: {item_e}")
                finally:
                    if downloaded_path and os.path.exists(downloaded_path):
                        os.remove(downloaded_path)

            await status_message.edit_text("✅ Semua story telah diproses!")
            await asyncio.sleep(3)
            await status_message.delete()

        except Exception as e:
            self._log.print(f"{self._log.RED}Gagal mengunduh story dari {username}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat memproses story: `{e}`")
