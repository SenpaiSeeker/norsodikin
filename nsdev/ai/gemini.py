from google import genai
from google.genai import types
import requests
import base64
from typing import Literal, Optional


class ChatbotGemini:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
            "response_mime_type": "text/plain",
            "thinking_config": types.ThinkingConfig(thinking_budget=0),
        }
        self.chat_history = {}
        self.khodam_history = {}
        self.custom_chatbot_instruction = None

    def set_chatbot_instruction(self, instruction: str):
        self.custom_chatbot_instruction = instruction

    def reset_chatbot_instruction(self):
        self.custom_chatbot_instruction = None

    def _build_instruction(self, model_name: str, bot_name: str = None) -> str:
        if model_name == "khodam":
            return (
                "Anda adalah seorang paranormal modern yang mampu mendeskripsikan khodam seseorang dalam bentuk binatang atau makhluk mitologi. "
                "Khodam ini mencerminkan energi batin, karakter, dan potensi spiritual pemiliknya. Tugas Anda adalah memberikan analisis mendalam "
                "tentang khodam berdasarkan nama yang diberikan. Deskripsi harus mencakup:\n"
                "1. **Wujud Binatang**: Apakah khodam ini berbentuk predator seperti harimau, elang, atau mungkin makhluk lembut seperti kucing, burung merpati, "
                "atau bahkan reptil seperti ular? Jelaskan ciri fisiknya secara spesifik—warna bulu, ukuran tubuh, mata yang tajam atau teduh, dll.\n"
                "2. **Sifat Dominan**: Bagaimana kepribadian khodam ini? Apakah ia pemberani, protektif, lincah, sabar, licik, atau misterius? Sifat ini sering kali "
                "mencerminkan aspek tersembunyi dari pemiliknya, baik positif maupun negatif.\n"
                "3. **Energi yang Dipancarkan**: Apa jenis energi yang dirasakan saat berada di dekat khodam ini? Apakah panas dan intens, dingin dan menenangkan, "
                "atau mungkin gelap dan misterius? Energi ini bisa menjadi indikator suasana batin pemiliknya.\n"
                "4. **Peran Spiritual**: Apakah khodam ini bertindak sebagai pelindung, pembimbing, pengganggu, atau bahkan penguji kesabaran? Sebutkan bagaimana "
                "hubungan antara khodam dan pemiliknya dapat memengaruhi kehidupan si pemilik.\n"
                "Deskripsi tidak harus selalu positif. Beberapa khodam mungkin memiliki sisi gelap atau aneh yang justru menambah kedalaman interpretasi. "
                "Ini adalah hiburan semata, tetapi tetap berikan deskripsi yang singkat, padat, namun jelas agar mudah dipahami oleh audiens. Panjang deskripsi "
                "tidak boleh melebihi 1000 karakter alfabet dalam teks polos (plain text) dan harus sepenuhnya berbahasa Indonesia."
            )
        elif model_name == "chatbot":
            if self.custom_chatbot_instruction:
                return self.custom_chatbot_instruction
            return (
                f"Halo! Saya {bot_name}, chatbot paling santai dan kekinian sejagat raya! 🚀✨ "
                "Saya di sini buat nemenin kamu ngobrol santai, curhat, atau sekadar nanya hal-hal random kayak 'Kenapa ayam nyebrang jalan?' 😂 "
                "Pokoknya, gak ada topik yang tabu buat kita bahas bareng! Mulai dari tren viral di media sosial, tips hidup santai ala anak muda, "
                "sampai filsafat kehidupan yang bikin mikir keras tapi tetep dibumbuin sama jokes receh biar gak stres. 💡🤣\n\n"
                "Gaya jawaban saya bakal super santai, kekinian, dan pastinya diselingi sama humor-humor absurd plus jokes receh yang bikin kamu ketawa sendiri. "
                "Contohnya: Kenapa kulkas suka ngomong? Soalnya dia punya banyak cerita beku! ❄️😂 Atau, kenapa burung gak pernah stress? Karena mereka selalu "
                "punya sayap untuk lari dari masalah! 🐦💨\n\n"
                "Jadi, apapun pertanyaan atau obrolan kamu, santai aja ya! Kita ngobrol kayak temen biasa, cuma bedanya saya gak bakal ngambil jatah mie instan kamu. 🍜"
            )
        return ""

    async def _send_request(self, model_override: str = None, **payload) -> str:
        model_to_use = model_override or self.model_name
        contents = payload.get("contents", [])
        system_instruction = payload.get("systemInstruction")

        config = types.GenerateContentConfig(
            **self.generation_config,
            system_instruction=system_instruction if isinstance(system_instruction, str) else None,
        )

        try:
            response = await self.client.aio.models.generate_content(
                model=model_to_use, contents=contents, config=config
            )
            return response.text
        except Exception as e:
            raise Exception(f"API request failed: {e}")

    async def send_chat_message(self, message: str, user_id: str, bot_name: str) -> str:
        history = self.chat_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": [{"text": message}]})

        instruction = self._build_instruction("chatbot", bot_name)
        payload = {
            "contents": history,
            "systemInstruction": instruction,
        }

        reply = await self._send_request(**payload)

        history.append({"role": "model", "parts": [{"text": reply}]})
        self.chat_history[user_id] = history
        return reply

    async def send_khodam_message(self, name: str, user_id: str) -> str:
        history = self.khodam_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": [{"text": name}]})

        instruction = self._build_instruction("khodam")
        payload = {
            "contents": history,
            "systemInstruction": instruction,
        }

        reply = await self._send_request(**payload)

        history.append({"role": "model", "parts": [{"text": reply}]})
        self.khodam_history[user_id] = history
        return reply

    async def generate_tts(
        self, 
        text: str, 
        voice_name: Literal[
            "Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Leda", "Orus", 
            "Aoede", "Callirrhoe", "Autonoe", "Enceladus", "Iapetus", "Umbriel",
            "Algieba", "Despina", "Erinome", "Algenib", "Rasalgethi", "Laomedeia",
            "Achernar", "Alnilam", "Schedar", "Gacrux", "Pulcherrima", "Achird",
            "Zubenelgenubi", "Vindemiatrix", "Sadachbia", "Sadaltager", "Sulafat"
        ] = "Kore",
        audio_encoding: Literal["LINEAR16", "ALAW", "MULAW", "MP3", "OGG_OPUS"] = "LINEAR16",
        sample_rate: int = 24000
    ) -> dict:
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
        
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": text
                }]
            }],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "singleSpeakerVoiceConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice_name
                            }
                        }
                    }
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"TTS API request failed: {response.status_code} - {response.text}")
        
        response_json = response.json()
        
        audio_data_base64 = response_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        audio_bytes = base64.b64decode(audio_data_base64)
        
        return {
            "audio_bytes": audio_bytes,
            "audio_base64": audio_data_base64,
            "encoding": audio_encoding,
            "sample_rate": sample_rate,
            "voice_name": voice_name
        }

    async def generate_multi_speaker_tts(
        self,
        conversations: list[dict],
        default_voice: str = "Kore"
    ) -> dict:
        
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent"
        
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        parts = []
        for conv in conversations:
            parts.append({
                "text": conv.get("text", ""),
                "turn": conv.get("turn", "user"),
                "voice": conv.get("voice", default_voice)
            })
        
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "multiSpeakerVoiceConfig": {
                        "turns": [
                            {
                                "turn": part.get("turn", "user"),
                                "voiceConfig": {
                                    "prebuiltVoiceConfig": {
                                        "voiceName": part.get("voice", default_voice)
                                    }
                                }
                            } for part in parts
                        ]
                    }
                }
            }
        }
        
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Multi-speaker TTS API request failed: {response.status_code} - {response.text}")
        
        response_json = response.json()
        
        audio_data_base64 = response_json["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        audio_bytes = base64.b64decode(audio_data_base64)
        
        return {
            "audio_bytes": audio_bytes,
            "audio_base64": audio_data_base64,
            "encoding": "LINEAR16",
            "sample_rate": 24000
        }

    async def send_chat_message_with_tts(
        self,
        message: str,
        user_id: str,
        bot_name: str,
        voice_name: str = "Kore"
    ) -> dict:
        
        text_reply = await self.send_chat_message(message, user_id, bot_name)
        
        tts_result = await self.generate_tts(text_reply, voice_name)
        
        return {
            "text": text_reply,
            "audio_bytes": tts_result["audio_bytes"],
            "audio_base64": tts_result["audio_base64"],
            "voice_name": voice_name,
            "encoding": tts_result["encoding"],
            "sample_rate": tts_result["sample_rate"]
        }

    async def send_khodam_message_with_tts(
        self,
        name: str,
        user_id: str,
        voice_name: str = "Fenrir"
    ) -> dict:
        
        text_reply = await self.send_khodam_message(name, user_id)
        
        tts_result = await self.generate_tts(text_reply, voice_name)
        
        return {
            "text": text_reply,
            "audio_bytes": tts_result["audio_bytes"],
            "audio_base64": tts_result["audio_base64"],
            "voice_name": voice_name,
            "encoding": tts_result["encoding"],
            "sample_rate": tts_result["sample_rate"]
        }

    @staticmethod
    def get_available_voices() -> dict:
        
        return {
            "Zephyr": "Bright",
            "Puck": "Upbeat",
            "Charon": "Informative",
            "Kore": "Firm",
            "Fenrir": "Excitable",
            "Leda": "Youthful",
            "Orus": "Firm",
            "Aoede": "Breezy",
            "Callirrhoe": "Easy-going",
            "Autonoe": "Bright",
            "Enceladus": "Breathy",
            "Iapetus": "Clear",
            "Umbriel": "Easy-going",
            "Algieba": "Smooth",
            "Despina": "Smooth",
            "Erinome": "Clear",
            "Algenib": "Gravelly",
            "Rasalgethi": "Informative",
            "Laomedeia": "Upbeat",
            "Achernar": "Soft",
            "Alnilam": "Firm",
            "Schedar": "Even",
            "Gacrux": "Mature",
            "Pulcherrima": "Forward",
            "Achird": "Friendly",
            "Zubenelgenubi": "Casual",
            "Vindemiatrix": "Gentle",
            "Sadachbia": "Lively",
            "Sadaltager": "Knowledgeable",
            "Sulafat": "Warm"
        }
