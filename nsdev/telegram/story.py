import asyncio
import uuid 
import os

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Document, Message, Photo

from ..utils.logger import LoggerHandler


class StoryDownloader:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()

    async def _process_and_send_story(self, story_item: types.StoryItem, target_chat_id: int):
        downloaded_path = None
        try:
            high_level_media = None
            send_method = None
            caption = story_item.caption.html if getattr(story_item, "caption", None) else ""

            if isinstance(story_item.media, types.MessageMediaPhoto):
                high_level_media = Photo._parse(self._client, story_item.media.photo)
                send_method = self._client.send_photo
            elif isinstance(story_item.media, types.MessageMediaDocument):
                high_level_media = Document._parse(self._client, story_item.media.document, f"story_{uuid.uuid4().hex[:9]}.mp4")
                send_method = self._client.send_video

            if high_level_media and send_method:
                downloaded_path = await self._client.download_media(high_level_media)
                await send_method(target_chat_id, downloaded_path, caption=caption)
                await asyncio.sleep(1.5)

        except Exception as item_e:
            self._log.warning(f"Gagal memproses satu story item: {item_e}")
        finally:
            if downloaded_path and os.path.exists(downloaded_path):
                os.remove(downloaded_path)

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

            story_ids = [s.id for s in getattr(peer_stories.stories, "stories", []) if isinstance(s, types.StoryItem)]

            if not story_ids:
                return await status_message.edit_text(f"✅ Pengguna `{username}` tidak memiliki story aktif (atau tidak dapat diakses).")

            total = len(story_ids)
            await status_message.edit_text(f"✅ Ditemukan {total} story aktif. Mengunduh dengan metode GetStoriesByID...")

            processed_count = 0
            for i, story_id in enumerate(story_ids):
                try:
                    await status_message.edit_text(f"📥 Mengambil story {i + 1}/{total}...")
                    story_data = await self._client.invoke(functions.stories.GetStoriesByID(peer=peer, id=[story_id]))

                    if not story_data.stories:
                        self._log.warning(f"Story ID {story_id} tidak dapat diakses.")
                        continue

                    story = story_data.stories[0]
                    if not isinstance(story, types.StoryItem):
                        self._log.warning(f"Story ID {story_id} bukan tipe StoryItem, dilewati.")
                        continue

                    await self._process_and_send_story(story, chat_id)
                    processed_count += 1
                    await asyncio.sleep(1.5)

                except Exception as story_err:
                    self._log.print(f"{self._log.YELLOW}Gagal memproses story ID {story_id}: {story_err}")

            if processed_count == 0:
                await status_message.edit_text(f"❌ Tidak ada story dari `{username}` yang dapat diunduh.")
            else:
                await status_message.edit_text(f"✅ Berhasil mengunduh {processed_count}/{total} story dari `{username}`!")

            await asyncio.sleep(3)
            await status_message.delete()

        except Exception as e:
            self._log.error(f"Gagal mengunduh story dari {username}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat memproses story: `{e}`")


    async def download_single_story(self, username: str, story_id: int, chat_id: int, status_message: Message):
        if self._client.me.is_bot:
            raise Exception("Bot accounts cannot download stories. This feature requires a Userbot.")

        try:
            await status_message.edit_text(f"Mencari pengguna `{username}`...")
            user = await self._client.get_users(username)
        except (UsernameInvalid, PeerIdInvalid):
            return await status_message.edit_text(f"❌ Pengguna `{username}` tidak ditemukan.")

        try:
            peer = await self._client.resolve_peer(user.id)
            story_data = await self._client.invoke(functions.stories.GetStoriesByID(peer=peer, id=[story_id]))
            
            if not story_data.stories:
                return await status_message.edit_text(f"❌ Story dengan ID `{story_id}` tidak ditemukan untuk `{username}`.")

            story = story_data.stories[0]
            if not isinstance(story, types.StoryItem):
                return await status_message.edit_text("❌ Story ini tidak dapat diakses atau telah kedaluwarsa.")
            
            await status_message.edit_text("📥 Mengunduh story...")
            await self._process_and_send_story(story, chat_id)
            
            await status_message.delete()

        except Exception as e:
            self._log.error(f"Gagal mengunduh story tunggal dari {username}: {e}")
            await status_message.edit_text(f"❌ Terjadi kesalahan saat mengunduh story: `{e}`")
