import asyncio
import os

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

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
            await status_message.edit_text(f"✅ Ditemukan {total} story aktif. Memulai pengiriman...")
            
            sent_count = 0
            for i, story in enumerate(active_stories):
                try:
                    caption = story.caption or ""
                    
                    if hasattr(story.media, "photo") and isinstance(story.media.photo, types.Photo):
                        await self._client.send_photo(chat_id, story.media.photo, caption=caption)
                        sent_count += 1
                    elif hasattr(story.media, "video") and isinstance(story.media.video, types.Video):
                        await self._client.send_video(chat_id, story.media.video, caption=caption)
                        sent_count += 1
                        
                    await status_message.edit_text(f"✈️ Mengirim story {i + 1}/{total}...")
                    await asyncio.sleep(1.5)

                except Exception as send_e:
                    self._log.print(f"{self._log.YELLOW}Gagal mengirim satu story: {send_e}")
                    continue

            final_message = f"✅ Selesai! Berhasil mengirim {sent_count} dari {total} story."
            await status_message.edit_text(final_message)
            await asyncio.sleep(5)
            await status_message.delete()

        except Exception as e:
            self._log.print(f"{self._log.RED}Gagal mengunduh story dari {username}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat mengunduh story: `{e}`")
