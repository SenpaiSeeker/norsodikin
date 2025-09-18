import os
import asyncio
import tempfile
import time
from functools import partial
import base64

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
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
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
            <div id="output"></div>
            <script>
                let recognition;
                window.startRecognition = function() {{
                    recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                    recognition.lang = '{self.lang}';
                    recognition.continuous = true;
                    recognition.interimResults = true;

                    recognition.onresult = function(event) {{
                        let final_transcript = '';
                        for (let i = 0; i < event.results.length; ++i) {{
                           final_transcript += event.results[i][0].transcript;
                        }}
                        document.getElementById('output').innerText = final_transcript;
                    }};
                    recognition.start();
                }};

                window.stopRecognition = function() {{
                    if (recognition) {{
                        recognition.stop();
                    }}
                }};
            </script>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=".html", encoding='utf-8') as f:
            f.write(html_code)
            self._html_path = f.name
    
    def _query_modifier(self, query: str) -> str:
        new_query = query.lower().strip()
        if not new_query: return ""
        if not new_query.endswith(('.', '!', '?')): new_query += '.'
        return new_query.capitalize()

    def _universal_translator(self, text: str) -> str:
        try: return mt.translate(text, "en", "auto")
        except: return text

    def _sync_transcribe(self, audio_bytes: bytes) -> str:
        if not self._driver or not self._html_path:
            raise RuntimeError("WebDriver tidak diinisialisasi dengan benar.")
            
        self._driver.get("file:///" + self._html_path)
        
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        js_script = f"""
        let audio_base64 = '{audio_base64}';
        let audio_data = atob(audio_base64);
        let array_buffer = new ArrayBuffer(audio_data.length);
        let view = new Uint8Array(array_buffer);
        for (let i = 0; i < audio_data.length; i++) {{
            view[i] = audio_data.charCodeAt(i);
        }}
        
        let audio_context = new (window.AudioContext || window.webkitAudioContext)();
        
        window.startRecognition();

        let audio_source = audio_context.createBufferSource();
        let media_stream_dest = audio_context.createMediaStreamDestination();
        audio_source.connect(media_stream_dest);

        // Dummy audio stream to trigger permission and start recognition
        recognition.mediaStream = media_stream_dest.stream;
        
        let recognized_text = '';

        audio_context.decodeAudioData(array_buffer, (buffer) => {{
            audio_source.buffer = buffer;
            audio_source.start(0);
        }});
        
        // Return promise to wait for result
        return new Promise((resolve) => {{
            recognition.onend = () => {{
                resolve(document.getElementById('output').innerText);
            }};
            setTimeout(() => {{
                recognition.stop();
            }}, 20000); // 20-second timeout for recognition
        }});
        """
        
        try:
            recognized_text = self._driver.execute_async_script(js_script)
        except:
            recognized_text = self._driver.find_element(By.ID, "output").text

        if not recognized_text:
            return ""

        if self.lang.lower().startswith("en"):
            return self._query_modifier(recognized_text)
        
        translated_text = self._universal_translator(recognized_text)
        return self._query_modifier(translated_text)

    async def transcribe(self, audio_bytes: bytes) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self._sync_transcribe, audio_bytes))
        
    def close(self):
        if self._driver:
            self._driver.quit()
        if self._html_path and os.path.exists(self._html_path):
            os.remove(self._html_path)
