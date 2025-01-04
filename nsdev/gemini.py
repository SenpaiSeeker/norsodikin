class ChatbotGemini:
    def __init__(self, api_key, bot_name="@NorSodikin"):
        self.genai = __import__("google.generativeai", fromlist=[""])
        self.genai.configure(api_key=api_key)

        self.generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        self.bot_name = bot_name
        self.chat_model = self.configure_model("chatbot")
        self.khodam_model = self.configure_model("khodam")

        self.chat_history = {}

    def configure_model(self, model_name):
        if model_name == "khodam":
            instruction = (
                "Halo! Saya di sini untuk membantu Anda memahami energi spiritual berdasarkan nama yang Anda berikan. "
                "Saya akan memberikan prediksi tentang sifat positif, negatif, rasio bintang, dan khodam dalam bentuk hewan. "
                "Ingat, ini hanya panduan spiritual yang dirancang untuk memberikan wawasan dan inspirasi. Nikmati prosesnya!"
            )
        else:
            instruction = (
                f"Yo, selamat datang! Nama gue {self.bot_name}, chatbot paling chill seantero galaksi! "
                "Gue di sini buat bantu lo curhat, nanya hal-hal serius, atau sekadar ngobrol santai. "
                "Tanya apa aja, dan gue bakal jawab dengan gaya yang kocak tapi tetep berbobot. "
                "Santai aja, kita ngobrol bareng dengan vibe asik dan hype! Let's goo!"
            )

        return self.genai.GenerativeModel(model_name="gemini-2.0-flash-exp", generation_config=self.generation_config, system_instruction=instruction)

    def send_chat_message(self, message, user_id):
        history = self.chat_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": message})

        response = self.chat_model.start_chat(history=history).send_message(message)
        history.append({"role": "assistant", "parts": response.text})

        return response.text

    def send_khodam_message(self, name):
        response = self.khodam_model.start_chat(history=[]).send_message(name)
        return response.text
