import os
import asyncio
import tempfile
from functools import partial

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import mtranslate as mt


class SpeechToText:
    def __init__(self, lang: str = "id-ID"):
        self.lang = lang
        self._driver = None
        self._html_path = None
        self._init_selenium()

    def _init_selenium(self):
        chrome_options = Options()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.142.86 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_argument("--headless=new")
        
        try:
            service = Service(ChromeDriverManager().install())
            self._driver = webdriver.Chrome(service=service, options=chrome_options)
        except Exception as e:
            raise RuntimeError(f"Gagal menginisialisasi WebDriver Chrome. Pastikan Chrome terinstal. Error: {e}")
            
        self._create_html_file()

    def _create_html_file(self):
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head><title>STT</title></head>
        <body>
            <button id="start" onclick="startRecognition()">Start</button>
            <button id="end" onclick="stopRecognition()">Stop</button>
            <div id="output"></div>
            <script>
                const output = document.getElementById('output');
                let recognition;
                function startRecognition() {{
                    recognition = new webkitSpeechRecognition() || new SpeechRecognition();
                    recognition.lang = '{self.lang}';
                    recognition.continuous = true;
                    recognition.onresult = function(event) {{
                        let final_transcript = '';
                        for (let i = 0; i < event.results.length; ++i) {{
                            final_transcript += event.results[i][0].transcript;
                        }}
                        output.innerHTML = final_transcript;
                    }};
                    recognition.start();
                }}
                function stopRecognition() {{
                    if (recognition) {{
                        recognition.stop();
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".html", encoding='utf-8') as f:
            f.write(html_code)
            self._html_path = f.name
    
    def _query_modifier(self, query: str) -> str:
        new_query = query.lower().strip()
        if not new_query:
            return ""
        
        question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom"]
        is_question = any(new_query.startswith(word) for word in question_words)

        if is_question:
            if not new_query.endswith('?'):
                new_query += '?'
        elif not new_query.endswith(('.', '!', '?')):
            new_query += '.'
            
        return new_query.capitalize()

    def _universal_translator(self, text: str) -> str:
        try:
            return mt.translate(text, "en", "auto")
        except Exception:
            return text

    def _sync_transcribe(self, audio_bytes: bytes) -> str:
        if not self._driver or not self._html_path:
            raise RuntimeError("WebDriver tidak diinisialisasi dengan benar.")

        audio_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='wb', suffix=".ogg") as f:
                f.write(audio_bytes)
                audio_file_path = f.name
            
            self._driver.get("file:///" + self._html_path)
            
            with open(audio_file_path, "rb") as f_audio:
                audio_base64 = self._driver.execute_script(
                    "let file = arguments[0];"
                    "let reader = new FileReader();"
                    "reader.readAsDataURL(file);"
                    "return new Promise(resolve => { reader.onload = () => resolve(reader.result); });",
                    webdriver.remote.webelement.WebElement(self._driver, 'file', w3c=True)
                )


            js_script = f"""
            let audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let audioData = atob('{audio_base64.split(",")[1]}');
            let arrayBuffer = new ArrayBuffer(audioData.length);
            let view = new Uint8Array(arrayBuffer);
            for (let i = 0; i < audioData.length; i++) {{
                view[i] = audioData.charCodeAt(i);
            }}

            audioContext.decodeAudioData(arrayBuffer, function(buffer) {{
                startRecognition();
                let source = audioContext.createBufferSource();
                source.buffer = buffer;
                let mediaStreamDest = audioContext.createMediaStreamDestination();
                source.connect(mediaStreamDest);
                
                recognition.onaudiostart = () => {{}}; 
                recognition.onaudioend = () => recognition.stop();
                
                source.start(0);
            }});
            """
            
            self._driver.execute_script(js_script)
            
            for _ in range(15):
                text = self._driver.find_element(By.ID, "output").text
                if text:
                    if self.lang.lower().startswith("en"):
                        return self._query_modifier(text)
                    else:
                        translated_text = self._universal_translator(text)
                        return self._query_modifier(translated_text)
                asyncio.sleep(1)
            return ""

        finally:
            if audio_file_path and os.path.exists(audio_file_path):
                os.remove(audio_file_path)

    async def transcribe(self, audio_bytes: bytes) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_transcribe, audio_bytes))
        
    def close(self):
        if self._driver:
            self._driver.quit()
        if self._html_path and os.path.exists(self._html_path):
            os.remove(self._html_path)
