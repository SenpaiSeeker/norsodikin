import asyncio
import os

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..logger import LoggerHandler 


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
            
            peer_stories = await self._client.invoke(
                functions.stories.GetPeerStories(
                    peer=peer
                )
            )

            active_stories = peer_stories.stories.stories

            if not active_stories:
                return await status_message.edit_text(f"✅ Pengguna `{username}` tidak memiliki story aktif.")
               

            total = len(active_stories)
            await status_message.edit_text(f"✅ Ditemukan {total} story aktif. Memulai pengunduhan...")
            
            for i, story in enumerate(active_stories):
                downloaded_path = None
                try:
                    await status_message.edit_text(f"📥 Mengunduh story {i + 1}/{total}...")
                    downloaded_path = await self._client.download_media(story)

                    caption = story.caption or ""

                    if isinstance(story.media, types.MessageMediaVideo):
                        await self._client.send_video(chat_id, downloaded_path, caption=caption)
                    elif isinstance(story.media, types.MessageMediaPhoto):
                        await self._client.send_photo(chat_id, downloaded_path, caption=caption)
                    
                    await asyncio.sleep(1.5)

                finally:
                    if downloaded_path and os.path.exists(downloaded_path):
                        os.remove(downloaded_path)

            await status_message.edit_text("✅ Semua story berhasil diunduh!")
            await asyncio.sleep(3)
            await status_message.delete()

        except Exception as e:
            self._log.print(f"{self._log.RED}Gagal mengunduh story dari {username}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat mengunduh story: `{e}`")
