import asyncio
from collections import Counter
from types import SimpleNamespace
from datetime import datetime
from zoneinfo import ZoneInfo

from pyrogram.types import Message


class ChatAnalyzer:
    def __init__(self):
        self.stop_words = {
            "di", "dan", "yg", "yang", "ga", "gak", "enggak", "ya", "itu", "ini", "ke", "aja", "saja",
            "ada", "sih", "sangat", "buat", "untuk", "dari", "dengan", "juga", "tapi", "kalau",
            "kalo", "lagi", "bisa", "udah", "sudah", "belum", "mau", "akan", "telah", "para", "jika"
        }

    async def analyze(self, messages: list[Message]) -> SimpleNamespace:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._run_analysis, messages)

    def _run_analysis(self, messages: list[Message]) -> SimpleNamespace:
        user_counter = Counter()
        word_counter = Counter()
        hour_counter = Counter()
        day_counter = Counter()
        user_map = {}

        jakarta_tz = ZoneInfo("Asia/Jakarta")

        for msg in messages:
            if msg.from_user and not msg.from_user.is_bot:
                user_id = msg.from_user.id
                user_counter[user_id] += 1
                if user_id not in user_map:
                    user_map[user_id] = msg.from_user.first_name or f"ID: {user_id}"

                local_time = msg.date.astimezone(jakarta_tz)
                hour_counter[local_time.hour] += 1
                day_counter[local_time.weekday()] += 1
            
            text_content = (msg.text or msg.caption or "").lower()
            words = text_content.split()
            for word in words:
                cleaned_word = ''.join(filter(str.isalpha, word))
                if cleaned_word and cleaned_word not in self.stop_words and len(cleaned_word) > 2:
                    word_counter[cleaned_word] += 1
        
        top_users = [
            {"name": user_map[uid], "count": count} for uid, count in user_counter.most_common(5)
        ]
        
        top_words = [
            {"word": word, "count": count} for word, count in word_counter.most_common(5)
        ]
        
        days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
        
        peak_hour = hour_counter.most_common(1)[0][0] if hour_counter else None
        peak_day_index = day_counter.most_common(1)[0][0] if day_counter else None
        peak_day = days[peak_day_index] if peak_day_index is not None else "N/A"
        
        return SimpleNamespace(
            total_messages=len(messages),
            top_users=top_users,
            top_words=top_words,
            peak_hour=peak_hour,
            peak_day=peak_day,
      )
