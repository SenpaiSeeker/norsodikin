# Pustaka Python `norsodikin`

[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan toolkit sakti buat kamu yang mau bikin bot Telegram super canggih, ngelola server, enkripsi data, sampai mainan AI, semuanya jadi lebih gampang dan seru.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas bisa kamu akses langsung lewat `client.ns`, bikin kode bot-mu jadi lebih bersih, rapi, dan intuitif.

## Instalasi

Instalasi `norsodikin` dilakukan langsung dari repositori GitHub untuk memastikan Anda mendapatkan versi terkini. Cukup instal apa yang Anda butuhkan.

**1. Instalasi Inti (Sangat Ringan)**
Perintah ini hanya akan menginstal pustaka inti dengan fitur dasar seperti `encrypt`, `payment`, `gemini`, `hf`, dan utilitas umum. Fitur-fitur lain memerlukan dependensi tambahan.

```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin"
```

**2. Instalasi dengan Fitur Tambahan (Extras)**
Gunakan "extras" untuk menambahkan dependensi bagi fitur-fitur spesifik. Anda bisa menggabungkan beberapa grup sekaligus.

*   **Untuk integrasi Pyrogram:**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[pyrogram]"
    ```
*   **Untuk semua fitur AI (TTS, Web Summarizer, Bing, Translate, QR Code, Vision, STT, Ollama):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[ai]"
    ```
    > **Catatan Penting untuk Pembaca QR Code:**
    > Fitur `qrcode.read()` memerlukan library `zbar`. Jika Anda menggunakan sistem berbasis Debian/Ubuntu, instal dengan perintah:
    > `sudo apt-get update && sudo apt-get install -y libzbar0`

*   **Untuk pengunduh media (YouTube, dll.):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[media]"
    ```

*   **Untuk monitoring server:**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[server]"
    ```
*   **Untuk menggunakan database MongoDB:**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[database]"
    ```
*   **Untuk utilitas CLI (seperti gradient banner):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[cli]"
    ```
*   **Menggabungkan beberapa fitur (contoh: Pyrogram + AI + Media):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[pyrogram,ai,media]"
    ```
*   **Instal Semua Fitur (Sakti Penuh):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[all]"
    ```

## Integrasi Ajaib dengan Pyrogram

Cukup `import nsdev`, dan semua keajaiban `norsodikin` akan otomatis menempel di objek `client` Pyrogram kamu lewat namespace `ns`. Semua modul kini dikelompokkan ke dalam namespace yang logis seperti `ai`, `telegram`, `data`, `utils`, dan `server` untuk membuat kode lebih terstruktur.

**Struktur Dasar**:

```python
import pyrogram
import nsdev  # Voila! Integrasi .ns langsung aktif

# Asumsikan 'client' adalah instance dari pyrogram.Client
# client = pyrogram.Client(...)

# Sekarang, semua modul siap pakai dalam namespace masing-masing:
client.ns.utils.log.info("Logger keren siap mencatat!")
# config = client.ns.data.yaml.loadAndConvert("config.yml")
# ...dan banyak lagi!
```

---

<details>
<summary><strong>Referensi API Lengkap (Klik untuk Buka/Tutup)</strong></summary>

Berikut adalah panduan mendalam untuk setiap modul yang tersedia.

### 1. `actions` -> `client.ns.telegram.actions`
Modul untuk menampilkan status *chat action* (seperti "typing...", "uploading photo...") secara otomatis selama sebuah proses berjalan. Ini memberikan feedback visual kepada pengguna bahwa bot sedang sibuk.

**Contoh Penggunaan Lengkap:**
```python
import asyncio

# @app.on_message(...)
async def long_process_handler(client, message):
    # Bot akan menampilkan status "typing..." selama 5 detik
    async with client.ns.telegram.actions.typing(message.chat.id):
        await asyncio.sleep(5)
```

---

### 2. `addUser` -> `client.ns.server.user`
Modul ini berfungsi sebagai manajer pengguna SSH jarak jauh di server Linux.

**Contoh Penggunaan Lengkap:**
```python
user_manager = client.ns.server.user(
    bot_token="TOKEN_BOT_TELEGRAM_ANDA", 
    chat_id=CHAT_ID_TUJUAN_ANDA
)
# Menambah pengguna dengan username dan password acak
user_manager.add_user()
```
**Catatan Penting:** Skrip ini memerlukan hak akses `sudo` untuk dapat menjalankan perintah `adduser` dan `deluser` di server.

---

### 3. `argument` -> `client.ns.telegram.arg`
Toolkit untuk mem-parsing dan mengekstrak informasi dari objek `message` Pyrogram.

**Contoh Penggunaan:**
```python
@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
    if user_id:
        print(f"User yang akan diban: {user_id}")
        print(f"Alasan: {reason or 'Tidak ada alasan'}")
```
---

### 4. `bing` -> `client.ns.ai.bing` (Tidak Stabil)
Generator gambar AI menggunakan Bing Image Creator. Karena ketergantungan pada *web scraping*, modul ini rentan terhadap perubahan dari sisi Bing. Gunakan dengan hati-hati.

**Contoh Penggunaan:**
```python
BING_COOKIE = "NILAI_COOKIE__U_ANDA"
bing_generator = client.ns.ai.bing(auth_cookie_u=BING_COOKIE)
prompt_gambar = "seekor rubah cyberpunk mengendarai motor di kota neon"
list_url = await bing_generator.generate(prompt=prompt_gambar)
print("URL gambar yang dihasilkan:", list_url)
```
---

### 5. `button` -> `client.ns.telegram.button`
Perkakas canggih untuk membuat `InlineKeyboardMarkup` dan `ReplyKeyboardMarkup` dengan sintaks yang intuitif, termasuk fitur paginasi otomatis.

**Membuat Inline Keyboard dari Teks**
```python
teks_inline = """
| 👤 Profil Saya - profil_user |
| 🌐 Website Kami - https://github.com/SenpaiSeeker/norsodikin |
"""
keyboard_inline, sisa_teks = client.ns.telegram.button.create_inline_keyboard(teks_inline)
# await message.reply(sisa_teks, reply_markup=keyboard_inline)
```

---

### 6. `database` -> `client.ns.data.db`
Sistem database fleksibel yang mendukung penyimpanan lokal (JSON), SQLite, dan MongoDB, dengan enkripsi data otomatis.

**Inisialisasi Database**
```python
# Opsi 1: JSON Lokal (Default, paling sederhana)
db = client.ns.data.db()
# Opsi 2: SQLite
db_sqlite = client.ns.data.db(storage_type="sqlite")
# Opsi 3: MongoDB
db_mongo = client.ns.data.db(storage_type="mongo", mongo_url="mongodb://user:pass@host:port/")
```

**Operasi Data Dasar (CRUD)**
```python
user_id = 12345
db.setVars(user_id, "nama", "Budi")
nama = db.getVars(user_id, "nama") # Output: Budi
```
---

### 7. `downloader` -> `client.ns.utils.downloader`
Utilitas canggih untuk mengunduh video atau audio dari berbagai platform (seperti YouTube, Instagram, dll) menggunakan `yt-dlp` sebagai backend.

**Struktur & Inisialisasi:**
Modul ini tidak memerlukan parameter saat inisialisasi.

**Contoh Penggunaan Lengkap:**
```python
# @app.on_message(filters.command("ytdl"))
async def download_media(client, message):
    if len(message.command) < 2:
        await message.reply("Sintaks: /ytdl [URL]")
        return
        
    url = message.command[1]
    status_msg = await message.reply("📥 Sedang memproses URL...")

    try:
        downloader = client.ns.utils.downloader
        
        # Download sebagai audio (format mp3)
        result = await downloader.download(url, audio_only=True)
        
        await status_msg.edit("⬆️ Mengunggah audio...")
        await client.send_audio(
            chat_id=message.chat.id,
            audio=result['path'],
            title=result['title'],
            duration=result['duration']
        )
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit(f"❌ Gagal mengunduh: {e}")
```
---

### 8. `encrypt` -> `client.ns.code`
Koleksi kelas untuk enkripsi dan dekripsi data dengan berbagai metode.

**Contoh Penggunaan:**
```python
cipher_bytes = client.ns.code.Cipher(key="kunci-rahasia", method="bytes")
data_asli = {"id": 123, "plan": "premium"}
terenkripsi_hex = cipher_bytes.encrypt(data_asli)
didekripsi_kembali = cipher_bytes.decrypt(terenkripsi_hex)
```
---

### 9. `formatter` -> `client.ns.telegram.formatter`
Builder canggih untuk menyusun pesan berformat dengan sintaks Markdown kustom atau mode HTML standar.

**Contoh Penggunaan:**
```python
fmt = client.ns.telegram.formatter("markdown")
pesan_terformat = (
    fmt.bold("🔥 Update Sistem").new_line()
    .text("Layanan telah kembali normal.").new_line()
    .italic("Terima kasih atas kesabaran Anda.")
    .to_string()
)
# await message.reply(pesan_terformat)
```
---

### 10. `gemini` -> `client.ns.ai.gemini`
Integrasi dengan Google Gemini API untuk fungsionalitas chatbot.

**Contoh Penggunaan:**
```python
chatbot = client.ns.ai.gemini(api_key="API_KEY_GEMINI_ANDA")
jawaban = chatbot.send_chat_message(
    message="jelaskan apa itu lubang hitam", 
    user_id="sesi_user_123", 
    bot_name="Bot Cerdas"
)
print(jawaban)
```
---

### 11. `gradient` -> `client.ns.utils.grad`
Mempercantik output terminal dengan teks bergradien dan timer countdown.

**Contoh Penggunaan:**
```python
# Menampilkan banner teks dengan warna gradien
client.ns.utils.grad.render_text("Norsodikin")
# Menjalankan timer countdown di terminal
await client.ns.utils.grad.countdown(seconds=10)
```
---

### 12. `hf` -> `client.ns.ai.hf` (Direkomendasikan)
Generator gambar AI stabil menggunakan Hugging Face Inference API.

**Contoh Penggunaan:**
```python
from io import BytesIO
HF_TOKEN = "hf_TOKEN_ANDA"
hf_generator = client.ns.ai.hf(api_key=HF_TOKEN)
prompt = "foto seorang astronot di pantai mars"
list_bytes = await hf_generator.generate(prompt)
file_gambar = BytesIO(list_bytes[0])
# await message.reply_photo(file_gambar)
```
---

### 13. `listen` -> `client.listen()` & `chat.ask()`
*Monkey-patching* untuk Pyrogram yang menambahkan alur percakapan interaktif.

**Aktivasi:** Cukup `from nsdev import listen` di awal skrip utama Anda.
**Contoh Penggunaan:**
```python
import asyncio
from nsdev import listen # Wajib di-import

# @app.on_message(filters.command("register"))
async def register(client, message):
    try:
        nama_msg = await message.chat.ask("Halo! Siapa namamu?", timeout=30)
        await message.reply(f"Senang bertemu, {nama_msg.text}!")
    except asyncio.TimeoutError:
        await message.reply("Waktu habis.")
```
---

### 14. `local` -> `client.ns.ai.local`
Jembatan untuk berinteraksi dengan model AI yang berjalan secara lokal di server Anda melalui **Ollama**. Memberikan privasi penuh dan tanpa biaya API.

**Penting:** Fitur ini mengharuskan Anda untuk menginstal dan menjalankan Ollama di server Anda terlebih dahulu.
> **[Lihat Panduan Lengkap Instalasi Ollama di Sini](OLLAMA_GUIDE.md)**

**Struktur & Inisialisasi:**
Jika Ollama berjalan di server yang sama dengan bot (kasus umum di VPS), tidak ada parameter yang dibutuhkan.
```python
# Inisialisasi sederhana
local_ai = client.ns.ai.local()

# Inisialisasi jika Ollama ada di server lain
# local_ai_remote = client.ns.ai.local(host="http://123.45.67.89:11434")
```
**Contoh Penggunaan Lengkap:**
```python
# @app.on_message(filters.command("asklocal"))
async def local_ai_handler(client, message):
    pertanyaan = message.text.split(None, 1)[1]
    if not pertanyaan:
        await message.reply("Tolong berikan pertanyaan. Contoh: /asklocal Siapa penemu bola lampu?")
        return

    status_msg = await message.reply("🧠 Berpikir...")
    
    try:
        local_ai = client.ns.ai.local()
        # Menggunakan model 'phi3:mini' yang lebih ringan dan cepat
        jawaban = await local_ai.chat(pertanyaan, model="phi3:mini")
        await status_msg.edit(jawaban)
    except Exception as e:
        await status_msg.edit(f"❌ Gagal terhubung ke Ollama: {e}\n\nPastikan Ollama sudah berjalan di server.")
```
---

### 15. `logger` -> `client.ns.utils.log`
Logger canggih pengganti `print()` yang memberikan output berwarna, berformat, dan informatif ke konsol.

**Penggunaan Dasar:**
```python
client.ns.utils.log.info("Memulai proses...")
client.ns.utils.log.debug(f"Data yang diterima: {data}")
client.ns.utils.log.error(f"Terjadi kesalahan: {e}")
```
---

### 16. `monitor` -> `client.ns.server.monitor`
Utilitas sederhana untuk memantau penggunaan sumber daya server Linux (CPU, RAM, Disk).

**Contoh Penggunaan:**
```python
stats = client.ns.server.monitor.get_stats()
pesan_status = (
    f"🖥️ **Status Server**\n"
    f"▫️ CPU: `{stats.cpu_percent}%`\n"
    f"▫️ RAM: `{stats.ram_used_gb:.2f}/{stats.ram_total_gb:.2f} GB`\n"
    f"▫️ Disk: `{stats.disk_used_gb:.2f}/{stats.disk_total_gb:.2f} GB`"
)
# await message.reply(pesan_status)
```
---

### 17. `payment` -> `client.ns.payment`
Klien terintegrasi untuk berbagai payment gateway populer di Indonesia.

**Contoh Midtrans:**
```python
midtrans = client.ns.payment.Midtrans(server_key="SERVER_KEY", client_key="CLIENT_KEY")
payment_info = midtrans.create_payment(order_id="order-123", gross_amount=50000)
print("URL Pembayaran:", payment_info.redirect_url)
```
---

### 18. `process` -> `client.ns.server.process`
Manajer untuk melihat dan mengelola proses yang berjalan di server Linux Anda. Berguna untuk memantau atau menghentikan aplikasi dari jarak jauh.

**Struktur & Inisialisasi:**
Modul ini tidak memerlukan parameter saat inisialisasi.

**Contoh Penggunaan Lengkap:**
```python
# @app.on_message(filters.command("top"))
async def top_processes(client, message):
    try:
        # Mengambil 5 proses dengan penggunaan memori tertinggi
        top_procs = await client.ns.server.process.list(limit=5, sort_by='memory_percent')
        
        fmt = client.ns.telegram.formatter("markdown")
        fmt.bold("🔥 Top 5 Proses Berdasarkan Memori").new_line(2)
        
        for p in top_procs:
            fmt.mono(f"PID: {p.pid:<5}").text(" | ")
            fmt.text(f"RAM: {p.memory_percent:.2f}% | ")
            fmt.bold(p.name).new_line()
        
        await message.reply(fmt.to_string())
        
        # Contoh cara menghentikan proses (gunakan dengan hati-hati!)
        # pid_to_kill = 12345
        # success = await client.ns.server.process.kill(pid_to_kill)
        # if success:
        #     await message.reply(f"Proses dengan PID {pid_to_kill} berhasil dihentikan.")
        
    except Exception as e:
        await message.reply(f"Gagal mengambil daftar proses: {e}")
```
---

### 19. `progress` -> `client.ns.utils.progress`
Callback helper untuk menampilkan progress bar dinamis saat mengunggah atau mengunduh file besar dengan Pyrogram.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("upload"))
async def upload_handler(client, message):
    pesan_status = await message.reply("🚀 Mempersiapkan unggahan...")
    progress_bar = client.ns.utils.progress(client, pesan_status)
    await client.send_video(
        chat_id=message.chat.id, 
        video="path/ke/video.mp4", 
        progress=progress_bar.update
    )
    await pesan_status.delete()
```
---

### 20. `qrcode` -> `client.ns.ai.qrcode`
Modul AI untuk membuat dan membaca gambar QR Code.

**Contoh Penggunaan:**
```python
from io import BytesIO
qr_manager = client.ns.ai.qrcode()
# Membuat QR
qr_bytes = await qr_manager.generate(data="https://github.com/SenpaiSeeker/norsodikin")
# Membaca QR dari data gambar (bytes)
# decoded_text = await qr_manager.read(image_data=gambar_bytes)
```
---

### 21. `shell` -> `client.ns.utils.shell`
Eksekutor perintah shell/terminal secara asinkron dari dalam Python.

**Contoh Penggunaan:**
```python
stdout, stderr, code = await client.ns.utils.shell.run("ls -l /home")
if code == 0:
    print(stdout)
else:
    print(stderr)
```
---

### 22. `stt` -> `client.ns.ai.stt`
Modul AI untuk Transkripsi Audio ke Teks (Speech-to-Text) menggunakan model Whisper dari Hugging Face. Sangat berguna untuk mengubah pesan suara menjadi teks.

**Struktur & Inisialisasi:**
Membutuhkan token API dari Hugging Face.
- **Parameter Wajib:**
  - `api_key` (`str`): Token API Hugging Face Anda (biasanya dimulai dengan `hf_`).

```python
stt_converter = client.ns.ai.stt(api_key="HF_TOKEN_ANDA")
```

**Contoh Penggunaan Lengkap:**
```python
# @app.on_message(filters.voice)
async def voice_to_text_handler(client, message):
    status_msg = await message.reply("🎤 Mendengarkan...")
    
    try:
        # Download pesan suara ke memori
        audio_file = await client.download_media(message.voice, in_memory=True)
        
        # Panggil modul STT untuk transkripsi
        stt_converter = client.ns.ai.stt(api_key="HF_TOKEN_ANDA")
        hasil_teks = await stt_converter.transcribe(audio_file.getvalue())
        
        if hasil_teks:
            await status_msg.edit(f"**Anda Mengatakan:**\n\n_{hasil_teks}_")
        else:
            await status_msg.edit("Maaf, saya tidak dapat memahami pesan suara Anda.")
            
    except Exception as e:
        await status_msg.edit(f"❌ Terjadi kesalahan saat transkripsi: {e}")
```
---

### 23. `storekey` -> `client.ns.data.key`
Manajer untuk menangani kunci rahasia dan nama file environment dari argumen terminal, mencegah *hardcoding* kredensial.

**Cara Menjalankan di Terminal:**
```python 
python3 main.py --key kunci-rahasia-anda --env config.env
```
---

### 24. `translate` -> `client.ns.ai.translate`
Modul AI untuk menerjemahkan teks ke berbagai bahasa menggunakan Google Translate API.

**Contoh Penggunaan:**
```python
translator = client.ns.ai.translate()
hasil_en = await translator.to("Selamat pagi", dest_lang="en")
print(hasil_en) # Output: Good morning
```
---

### 25. `tts` -> `client.ns.ai.tts`
Modul AI untuk mengubah teks menjadi pesan suara (Text-to-Speech).

**Contoh Penggunaan:**
```python
from io import BytesIO
tts_generator = client.ns.ai.tts()
audio_bytes = await tts_generator.generate(text="Halo, ini adalah pesan suara.", lang="id")
file_suara = BytesIO(audio_bytes)
file_suara.name = "pesan.ogg"
# await message.reply_voice(file_suara)
```
---

### 26. `url` -> `client.ns.utils.url`
Utilitas sederhana untuk memendekkan URL menggunakan layanan TinyURL.

**Contoh Penggunaan:**
```python
url_panjang = "https://github.com/SenpaiSeeker/norsodikin"
url_pendek = await client.ns.utils.url.shorten(url_panjang)
print(url_pendek)
```
---

### 27. `vision` -> `client.ns.ai.vision`
Modul AI yang mampu "melihat" dan memahami konten gambar menggunakan model Gemini Vision. Bisa digunakan untuk mendeskripsikan gambar atau menjawab pertanyaan tentang gambar.

**Struktur & Inisialisasi:**
- **Parameter Wajib:**
  - `api_key` (`str`): Kunci API Google Gemini Anda.

```python
vision_analyzer = client.ns.ai.vision(api_key="GEMINI_API_KEY_ANDA")
```

**Contoh Penggunaan Lengkap:**
```python
# @app.on_message(filters.photo)
async def analyze_image_handler(client, message):
    status_msg = await message.reply("👀 Menganalisis gambar...")
    
    try:
        # Download foto ke memori
        photo_bytes_io = await client.download_media(message.photo, in_memory=True)
        
        vision_analyzer = client.ns.ai.vision(api_key="GEMINI_API_KEY_ANDA")
        
        # Opsi 1: Mendeskripsikan gambar
        deskripsi = await vision_analyzer.describe(photo_bytes_io.getvalue())
        await status_msg.edit(f"**Deskripsi Gambar:**\n\n{deskripsi}")
        
        # Opsi 2: Menjawab pertanyaan spesifik tentang gambar (jika ada caption)
        if message.caption and message.caption.lower().startswith("tanya:"):
            pertanyaan = message.caption[6:].strip()
            jawaban = await vision_analyzer.ask(
                image_bytes=photo_bytes_io.getvalue(),
                question=pertanyaan
            )
            await message.reply(f"**Jawaban:**\n{jawaban}")

    except Exception as e:
        await status_msg.edit(f"❌ Gagal menganalisis gambar: {e}")
```
---

### 28. `web` -> `client.ns.ai.web`
Alat AI canggih untuk melakukan *scraping* konten teks dari sebuah URL dan merangkumnya menggunakan model Gemini.

**Contoh Penggunaan:**
```python
gemini_bot = client.ns.ai.gemini(api_key="GEMINI_API_KEY_ANDA")
web_summarizer = client.ns.ai.web(gemini_instance=gemini_bot)
url_berita = "https://www.kompas.com/..."
rangkuman = await web_summarizer.summarize(url_berita)
# await message.reply(f"**Rangkuman Artikel:**\n\n{rangkuman}")
```
---

### 29. `ymlreder` -> `client.ns.data.yaml`
Utilitas praktis untuk membaca file konfigurasi `.yml` dan mengubahnya menjadi objek Python yang bisa diakses dengan notasi titik (`.`).

**Contoh Kode:**
```python
# Muat file config.yml
config = client.ns.data.yaml.loadAndConvert("config.yml")
if config:
    print(f"Nama Aplikasi: {config.app.name}")
    print(f"Host Database: {config.database.host}")
```
---
</details>

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, kamu bebas pakai, modifikasi, dan distribusikan untuk proyek apa pun.

---

Semoga dokumentasi ini bikin kamu makin semangat ngoding! Selamat mencoba dan berkreasi dengan `norsodikin`. Jika ada pertanyaan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
```
