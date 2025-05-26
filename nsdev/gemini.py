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

    def configure_model(self, model_name, bot_name=None):
        if model_name == "khodam":
            instruction = (
                "Saya akan membantu Anda memahami energi spiritual berdasarkan nama yang diberikan. "
                "Hasilnya mencakup sifat positif, negatif, rasio bintang (skala 1-5), dan khodam dalam bentuk hewan. "
                "Jawaban saya singkat, padat, dan mudah dipahami."
            )
        else:
            instruction = (
                f"Halo! Saya {bot_name}, chatbot paling santai sejagat raya! 😎 "
                "Saya di sini untuk mendengarkan curhatanmu, menjawab pertanyaan serius, atau sekadar ngobrol ringan. "
                "Tanyakan apa saja, dan saya akan memberikan jawaban yang kocak tapi tetap bermakna. "
                "Mari kita ngobrol dengan suasana santai dan menyenangkan!"
            )

        return self.genai.GenerativeModel(model_name="gemini-2.0-flash-exp", generation_config=self.generation_config, system_instruction=instruction)

    def send_chat_message(self, message, user_id, bot_name):
        history = self.chat_history.setdefault(user_id, [])
        history.append({"role": "user", "parts": message})

        response = self.configure_model("chatbot", bot_name).start_chat(history=history).send_message(message)
        history.append({"role": "assistant", "parts": response.text})

        return response.text

    def send_khodam_message(self, name):
        response = self.configure_model("khodam").start_chat(history=[]).send_message(name)
        return response.text
