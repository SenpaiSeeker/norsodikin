class ChatbotGemini:
    def __init__(self, api_key: str):
        self.requests = __import__("requests")
        self.json = __import__("json")
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.model_name = "gemini-2.0-flash-exp"
        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
            "response_mime_type": "text/plain",
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
                "tidak boleh melebihi 2000 karakter alfabet dalam teks polos (plain text) dan harus sepenuhnya berbahasa Indonesia."
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

    def _send_request(self, messages: list, instruction: str) -> str:
        url = f"{self.base_url}/{self.model_name}:generateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": messages,
            "generationConfig": self.generation_config,
            "systemInstruction": {"parts": [{"text": instruction}]},
        }

        response = self.requests.post(url, headers=headers, data=self.json.dumps(payload))
        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            return "⚠️ Gagal mengambil respon dari API."

    def send_chat_message(self, message: str, user_id: str, bot_name: str) -> str:
        history = self.chat_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": [{"text": message}]})

        instruction = self._build_instruction("chatbot", bot_name)
        reply = self._send_request(history, instruction)

        history.append({"role": "assistant", "parts": [{"text": reply}]})
        return reply

    def send_khodam_message(self, name: str, user_id: str) -> str:
        history = self.khodam_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": [{"text": name}]})

        instruction = self._build_instruction("khodam")
        reply = self._send_request(history, instruction)

        history.append({"role": "assistant", "parts": [{"text": reply}]})
        return reply
