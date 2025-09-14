import asyncio

from pyrogram.errors import PeerIdInvalid, RPCError, UsernameInvalid
from pyrogram.raw import functions, types
from pyrogram.types import Message

from ..utils.logger import LoggerHandler


class StoryDownloader:
    def __init__(self, client):
        self._client = client
        self._log = LoggerHandler()
    
    async def _build_fake_message(self, story_item, peer_stories):
        fake_message = await self._client.build_object(
            types.Message,
            props={
                'id': story_item.id,
                'peer_id': peer_stories.peer,
                'date': story_item.date,
                'message': story_item.caption or "",
                'media': story_item.media,
                'entities': story_item.entities,
                'out': story_item.out,
                'from_id': peer_stories.peer,
            },
            origin="stories.getPeerStories"
        )
        return fake_message


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
                    fake_message_with_media = await self._build_fake_message(story, peer_stories)
                    
                    if fake_message_with_media.media:
                        await fake_message_with_media.copy(chat_id)
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
