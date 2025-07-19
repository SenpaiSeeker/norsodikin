class ChatbotGemini:
    def __init__(self, api_key):
        self.genai = __import__("google.generativeai", fromlist=[""])
        self.genai.configure(api_key=api_key)

        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
            "response_mime_type": "text/plain",
        }
        self.chat_history = {}
        self.khodam_history = {}

    def configure_model(self, model_name, bot_name=None):
        if model_name == "khodam":
            instruction = (
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
        else:
            instruction = (
                f"Halo! Saya {bot_name}, chatbot paling santai dan kekinian sejagat raya! 🚀✨ "
                "Saya di sini buat nemenin kamu ngobrol santai, curhat, atau sekadar nanya hal-hal random kayak 'Kenapa ayam nyebrang jalan?' 😂 "
                "Pokoknya, gak ada topik yang tabu buat kita bahas bareng! Mulai dari tren viral di media sosial, tips hidup santai ala anak muda, "
                "sampai filsafat kehidupan yang bikin mikir keras tapi tetep dibumbuin sama jokes receh biar gak stres. 💡🤣\n\n"
                "Gaya jawaban saya bakal super santai, kekinian, dan pastinya diselingi sama humor-humor absurd plus jokes receh yang bikin kamu ketawa sendiri. "
                "Contohnya: Kenapa kulkas suka ngomong? Soalnya dia punya banyak cerita beku! ❄️😂 Atau, kenapa burung gak pernah stress? Karena mereka selalu "
                "punya sayap untuk lari dari masalah! 🐦💨\n\n"
                "Jadi, apapun pertanyaan atau obrolan kamu, santai aja ya! Kita ngobrol kayak temen biasa, cuma bedanya saya gak bakal ngambil jatah mie instan kamu. 🍜"
            )

        return self.genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config=self.generation_config,
            system_instruction=instruction,
        )

    def send_chat_message(self, message, user_id, bot_name):
        history = self.chat_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": message})

        response = self.configure_model("chatbot", bot_name).start_chat(history=history).send_message(message)
        history.append({"role": "assistant", "parts": response.text})

        return response.text

    def send_khodam_message(self, name, user_id):
        history = self.khodam_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": name})

        response = self.configure_model("khodam").start_chat(history=history).send_message(name)
        history.append({"role": "assistant", "parts": response.text})

        return response.text
