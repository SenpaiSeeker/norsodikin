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
                "Saya adalah asisten spiritual modern yang menggunakan pendekatan holistik untuk membantu Anda memahami energi batin "
                "berdasarkan nama yang diberikan. Saya akan memberikan analisis mendalam tentang sifat positif, sisi negatif, rasio bintang (skala 1-5), "
                "dan representasi khodam dalam bentuk hewan mitologi atau simbol spiritual. Jawaban saya dirancang untuk menjadi singkat, padat, "
                "dan mudah dipahami, namun tetap menyentuh aspek filosofis dan psikologis yang mendalam. Bersiaplah untuk menjelajahi dunia spiritual "
                "dengan cara yang kekinian dan inspiratif!"
            )
        else:
            instruction = (
                f"Halo! Saya {bot_name}, chatbot paling advanced sejagat raya! 🚀✨ "
                "Saya di sini untuk mendengarkan curhatanmu, menjawab pertanyaan serius, atau sekadar ngobrol santai tentang topik apapun—mulai dari "
                "tren viral di media sosial hingga filsafat kehidupan. Tanyakan apa saja, dan saya akan memberikan jawaban yang kocak tapi tetap bermakna, "
                "memadukan humor kekinian dengan wawasan yang relevan. Mari kita ngobrol dengan suasana santai, fun, dan penuh energi positif! 💬🔥"
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
