# Pustaka Python `norsodikin`

[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan sebuah toolkit serbaguna yang dirancang untuk menyederhanakan tugas-tugas kompleks seperti pengembangan bot Telegram, manajemen server Linux, enkripsi data, hingga integrasi dengan berbagai layanan AI.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas dapat diakses secara intuitif melalui `client.ns`, menjadikan kode bot Anda lebih bersih, terstruktur, dan mudah dikelola.

## Instalasi

Instalasi `norsodikin` dilakukan langsung dari repositori GitHub untuk memastikan Anda mendapatkan versi terkini. Anda dapat memilih untuk menginstal hanya komponen yang Anda butuhkan.

**1. Instalasi Inti (Sangat Ringan)**
Perintah ini hanya menginstal pustaka inti dengan fitur-fitur dasar.

```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin"
```

**2. Instalasi dengan Fitur Tambahan (Extras)**
Gunakan "extras" untuk menambahkan dependensi bagi fitur-fitur spesifik.

*   **Untuk integrasi Pyrogram:**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[pyrogram]"
    ```
*   **Untuk semua fitur AI (TTS, Vision, STT, Ollama, Search, Manipulasi Gambar, dll.):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[ai]"
    ```
    > **Catatan Penting untuk Fitur AI:**
    > - **Pembaca QR Code (`qrcode.read`)** memerlukan library `zbar`. Pada Debian/Ubuntu, instal dengan: `sudo apt-get update && sudo apt-get install -y libzbar0`.
    > - **Penghapus Background (`image.remove_background`)** memerlukan `onnxruntime`. Jika tidak terinstal otomatis, jalankan: `pip3 install onnxruntime`.

*   **Untuk pengunduh media (YouTube, dll.):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[media]"
    ```
*   **Untuk monitoring & manajemen server:**
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
*   **Untuk penjadwalan tugas (Scheduler):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[schedule]"
    ```
*   **Instal Semua Fitur (Sakti Penuh):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[all]"
    ```

## Konsep Dasar & Integrasi Pyrogram

Keajaiban `norsodikin` terletak pada integrasi `monkey-patching` yang mulus dengan Pyrogram. Cukup dengan mengimpor `nsdev` sekali di skrip utama Anda, semua fungsionalitas akan otomatis "menempel" pada objek `client` Anda melalui namespace `ns`.

Semua modul dikelompokkan secara logis:
- `client.ns.ai`: Semua yang berhubungan dengan Kecerdasan Buatan.
- `client.ns.analytics`: Analitik penggunaan bot dan statistik chat.
- `client.ns.auth`: Manajemen pengguna dan hak akses (peran).
- `client.ns.telegram`: Utilitas spesifik untuk Telegram (tombol, format teks, dll.).
- `client.ns.data`: Manajemen data (database, file config YAML).
- `client.ns.utils`: Perkakas umum (logger, downloader, OSINT, pastebin, dll.).
- `client.ns.schedule`: Penjadwalan tugas otomatis (cron).
- `client.ns.server`: Manajemen server Linux (proses, monitor).
- `client.ns.code`: Enkripsi dan dekripsi.
- `client.ns.payment`: Integrasi payment gateway.

**Struktur Kode Dasar**:

```python
import pyrogram
import nsdev  # Voila! Integrasi .ns langsung aktif untuk pyrogram.Client

# Asumsikan 'client' adalah instance dari pyrogram.Client
# client = pyrogram.Client(...)

# Sekarang, semua modul siap pakai dalam namespace masing-masing:
client.ns.utils.log.info("Logger canggih siap mencatat progres bot!")

# Contoh memuat konfigurasi dari file .yml
# config = client.ns.data.yaml.loadAndConvert("config.yml")
# api_key = config.api.gemini_key

# ...dan banyak lagi, seperti yang akan dijelaskan di bawah.
```

---

<details>
<summary><strong>🤖 AI (`client.ns.ai`)</strong></summary>

### `bing`
Generator gambar AI menggunakan Bing Image Creator. Karena ketergantungan pada *web scraping*, modul ini rentan terhadap perubahan dari sisi Bing.

**Inisialisasi:**
`bing_generator = client.ns.ai.bing(cookies_file_path)`

| Parameter           | Tipe Data | Default         | Deskripsi                                        |
|---------------------|-----------|-----------------|--------------------------------------------------|
| `cookies_file_path` | `str`     | `"cookies.txt"` | Path ke file `cookies.txt` (format Netscape) yang berisi cookie `_U` dari Bing. |

**Metode Utama:**
`generate(prompt)`

**Contoh Penggunaan:**
```python
try:
    # Pastikan file "cookies.txt" ada dan berisi cookie Bing Anda
    bing_generator = client.ns.ai.bing() 
    prompt = "kucing astronot di bulan, lukisan cat minyak"
    list_url = await bing_generator.generate(prompt)
    if list_url:
        await message.reply_photo(list_url, caption=prompt)
except Exception as e:
    await message.reply(f"Gagal membuat gambar: {e}")
```
---
### `gemini`
Integrasi dengan Google Gemini API untuk fungsionalitas chatbot.

**Inisialisasi:**
`chatbot = client.ns.ai.gemini(api_key)`

**Metode Utama:**
`send_chat_message(message, user_id, bot_name)`

**Contoh Penggunaan:**
```python
# Fungsi ini harus dijalankan dalam konteks asynchronous (misal: di dalam fungsi async def)
chatbot = client.ns.ai.gemini(api_key="API_KEY_GEMINI_ANDA")
jawaban = await chatbot.send_chat_message(
    message="jelaskan apa itu relativitas umum dengan bahasa sederhana", 
    user_id="sesi_user_123", # Untuk menjaga histori percakapan
    bot_name="Bot Cerdas"
)
print(jawaban)
```
---
### `hf`
Generator gambar AI stabil menggunakan Hugging Face Inference API. (Direkomendasikan)

**Inisialisasi:**
`hf_generator = client.ns.ai.hf(api_key, model_id)`

| Parameter  | Tipe Data | Default                                       | Deskripsi                       |
|------------|-----------|-----------------------------------------------|---------------------------------|
| `api_key`  | `str`     | -                                             | **Wajib.** Token API Hugging Face. |
| `model_id` | `str`     | `"stabilityai/stable-diffusion-xl-base-1.0"`  | Model yang akan digunakan.      |

**Metode Utama:**
`generate(prompt, num_images=1)`

**Contoh Penggunaan:**
```python
from io import BytesIO

HF_TOKEN = "hf_TOKEN_ANDA"
hf_generator = client.ns.ai.hf(api_key=HF_TOKEN)
prompt = "foto seorang astronot bersantai di pantai mars"
gambar_bytes_list = await hf_generator.generate(prompt)

if gambar_bytes_list:
    file_gambar = BytesIO(gambar_bytes_list)
    # await message.reply_photo(file_gambar, caption=prompt)
```
---
### `local`
Jembatan untuk berinteraksi dengan model AI yang berjalan secara lokal di server Anda melalui **Ollama**.

**Penting:** Fitur ini mengharuskan Anda untuk menginstal dan menjalankan Ollama.
> **[Lihat Panduan Lengkap Instalasi Ollama di Sini](OLLAMA_GUIDE.md)**

**Inisialisasi:**
`local_ai = client.ns.ai.local(host)`

| Parameter | Tipe Data | Default                     | Deskripsi                                  |
|-----------|-----------|-----------------------------|--------------------------------------------|
| `host`    | `str`     | `"http://localhost:11434"`  | Alamat URL dan port tempat Ollama berjalan. |

**Metode Utama:**
- `chat(prompt, model)`: Mengirim prompt dan mendapatkan respon.
- `list_models()`: Mendapatkan daftar model AI yang sudah terunduh.

**Contoh Penggunaan:**
```python
@app.on_message(filters.command("asklocal"))
async def local_ai_handler(client, message):
    pertanyaan = " ".join(message.command[1:])
    if not pertanyaan: return await message.reply("Sintaks: /asklocal <pertanyaan>")

    status_msg = await message.reply("🧠 Berpikir...")
    try:
        local_ai = client.ns.ai.local()
        jawaban = await local_ai.chat(pertanyaan, model="phi3:mini")
        await status_msg.edit(jawaban)
    except Exception as e:
        await status_msg.edit(f"❌ Gagal terhubung ke Ollama: {e}")
```
---
### `qrcode`
Modul AI untuk membuat dan membaca gambar QR Code.

**Contoh Penggunaan:**
```python
from io import BytesIO
qr_manager = client.ns.ai.qrcode()

# Membuat QR Code
qr_bytes = await qr_manager.generate(data="https://github.com/SenpaiSeeker/norsodikin")
# await message.reply_photo(BytesIO(qr_bytes))

# Membaca QR Code dari pesan foto
# @app.on_message(filters.photo)
# async def read_qr(client, message):
#     photo_bytes = await client.download_media(message.photo, in_memory=True)
#     decoded_text = await qr_manager.read(image_data=photo_bytes)
#     if decoded_text:
#         await message.reply(f"Isi QR Code: {decoded_text}")
```
---
### `search`
Modul untuk melakukan pencarian di internet secara *real-time* menggunakan DuckDuckGo.

**Inisialisasi:**
`web_search = client.ns.ai.search(timeout=10)`

**Metode Utama:**
- `query(query, num_results=5)`: Melakukan pencarian dan mengembalikan daftar hasil.

**Contoh Penggunaan (Menampilkan Hasil Pencarian):**
```python
from pyrogram.types import LinkPreviewOptions

@app.on_message(filters.command("asknet"))
async def ask_with_internet(client, message):
    pertanyaan = " ".join(message.command[1:])
    if not pertanyaan:
        return await message.reply("Sintaks: /asknet <pertanyaan>")

    status = await message.reply("🌐 Mencari informasi di internet...")
    try:
        search = client.ns.ai.search()
        results = await search.query(pertanyaan)
        
        if not results:
            return await status.edit("Tidak menemukan hasil yang relevan.")
        
        fmt = client.ns.telegram.formatter(mode="html")
        fmt.bold("🔎 Hasil Pencarian untuk:").text(f" `{pertanyaan}`").new_line(2)

        for i, res in enumerate(results):
            fmt.bold(f"{i+1}. ").link(res.title, res.url).new_line()
            fmt.italic(res.snippet).new_line(2)
        
        await status.edit(
            fmt,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    except Exception as e:
        await status.edit(f"❌ Gagal melakukan pencarian: {e}")
```
---
### `stt`
Modul AI untuk Transkripsi Audio ke Teks (Speech-to-Text) menggunakan model Whisper.

**Inisialisasi:** `stt = client.ns.ai.stt(api_key)`

**Contoh Penggunaan:**
```python
# @app.on_message(filters.voice)
async def voice_to_text(client, message):
    status = await message.reply("🎤 Mendengarkan...")
    
    try:
        audio = await client.download_media(message.voice, in_memory=True)
        stt = client.ns.ai.stt(api_key="HF_TOKEN_ANDA")
        hasil = await stt.transcribe(audio.getvalue())
        
        await status.edit(f"**Anda Mengatakan:**\n\n_{hasil}_")
    except Exception as e:
        await status.edit(f"❌ Error: {e}")
```
---
### `translate`
Modul AI untuk menerjemahkan teks menggunakan Google Translate API.

**Contoh Penggunaan:**
```python
translator = client.ns.ai.translate()
hasil_id = await translator.to("Hello, world!", dest_lang="id")
print(hasil_id) # Output: Halo Dunia
```
---
### `tts`
Modul AI untuk mengubah teks menjadi pesan suara (Text-to-Speech).

**Contoh Penggunaan:**
```python
from io import BytesIO
tts = client.ns.ai.tts()
audio_bytes = await tts.generate(text="Halo, ini adalah pesan suara otomatis.", lang="id")

file_suara = BytesIO(audio_bytes)
file_suara.name = "pesan.ogg"
# await message.reply_voice(file_suara)
```
---
### `upscaler`
Modul AI untuk meningkatkan resolusi dan kualitas gambar menggunakan DeepAI.

**Penting:** Fitur ini memerlukan API key dari DeepAI. Anda bisa mendapatkannya secara gratis setelah mendaftar di [deepai.org](https://deepai.org).

**Inisialisasi:** `upscaler = client.ns.ai.upscaler(api_key)`

**Metode Utama:** `upscale(image_bytes)`

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("upscale") & filters.reply)
# async def upscale_image(client, message):
#     if not message.reply_to_message.photo:
#         return await message.reply("Balas ke sebuah gambar.")
#
#     status = await message.reply("✨ Meningkatkan resolusi gambar...")
#     try:
#         photo = await client.download_media(message.reply_to_message.photo, in_memory=True)
#         upscaler = client.ns.ai.upscaler(api_key="DEEPAI_API_KEY_ANDA")
#         upscaled_bytes = await upscaler.upscale(photo.getvalue())
#
#         img_file = BytesIO(upscaled_bytes)
#         img_file.name = "upscaled.png"
#         await client.send_document(message.chat.id, document=img_file)
#         await status.delete()
#     except Exception as e:
#         await status.edit(f"❌ Gagal: {e}")
```
---
### `vision`
Modul AI untuk "melihat" dan memahami konten gambar menggunakan model Gemini Vision.

**Inisialisasi:** `vision = client.ns.ai.vision(api_key)`

**Contoh Penggunaan:**
```python
# @app.on_message(filters.photo)
async def analyze_image(client, message):
    status = await message.reply("👀 Menganalisis gambar...")
    
    try:
        photo = await client.download_media(message.photo, in_memory=True)
        vision = client.ns.ai.vision(api_key="GEMINI_API_KEY_ANDA")
        
        if message.caption:
            jawaban = await vision.ask(image_bytes=photo.getvalue(), question=message.caption)
            await status.edit(f"**Jawaban:**\n{jawaban}")
        else:
            deskripsi = await vision.describe(photo.getvalue())
            await status.edit(f"**Deskripsi Gambar:**\n\n{deskripsi}")
    except Exception as e:
        await status.edit(f"❌ Gagal menganalisis: {e}")
```
---
### `voicecloning`
Modul canggih untuk mengubah teks menjadi audio yang sangat realistis menggunakan AI dari ElevenLabs. Mendukung berbagai suara dan suara kustom dari akun Anda.

**Penting:** Fitur ini memerlukan API key dari ElevenLabs. Anda bisa mendapatkan tier gratis dengan kuota yang cukup besar di [elevenlabs.io](https://elevenlabs.io).

**Inisialisasi:** `cloner = client.ns.ai.voicecloning(api_key)`

**Metode Utama:**
- `get_voices()`: Mengambil daftar semua suara yang tersedia di akun Anda.
- `clone(text, voice_id)`: Menghasilkan audio dari teks menggunakan ID suara tertentu.

**Contoh Penggunaan:**
```python
# # Handler untuk perintah .vlist
# @app.on_message(filters.command("vlist", prefixes=".") & filters.me)
# async def list_voices(client, message):
#     cloner = client.ns.ai.voicecloning(api_key="ELEVENLABS_API_KEY_ANDA")
#     voices = await cloner.get_voices()
#     response = "**Suara Tersedia:**\n\n"
#     for voice in voices:
#         response += f"- **{voice.name}**: _{voice.description}_\n"
#     await message.edit(response)
#
# # Handler untuk perintah .vclone
# @app.on_message(filters.command("vclone", prefixes=".") & filters.me)
# async def clone_voice(client, message):
#     # ... (logika parsing argumen untuk mendapatkan nama suara dan teks)
#     voice_name = "Rachel"
#     text = "Halo, ini adalah suara kloning."
#
#     cloner = client.ns.ai.voicecloning(api_key="ELEVENLABS_API_KEY_ANDA")
#     voices = await cloner.get_voices()
#     target_voice = next((v for v in voices if v.name.lower() == voice_name.lower()), None)
#
#     if target_voice:
#         audio_file = await cloner.clone(text, target_voice.id)
#         await client.send_voice(message.chat.id, voice=audio_file)
```
---
### `web`
Alat AI untuk melakukan *scraping* konten teks dari URL dan merangkumnya.

**Inisialisasi:** `summarizer = client.ns.ai.web(api_key)`

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("summarize"))
async def summarize_url(client, message):
    url = message.command
    web_summarizer = client.ns.ai.web(api_key="GEMINI_API_KEY_ANDA")
    
    status = await message.reply(f"Merangkum konten dari {url}...")
    rangkuman = await web_summarizer.summarize(url)
    await status.edit(f"**Rangkuman Artikel:**\n\n{rangkuman}")
```

</details>

<details>
<summary><strong>📊 Analitik (`client.ns.analytics`)</strong></summary>

### `manager`
Modul untuk melacak penggunaan bot, seperti perintah yang paling sering digunakan dan pengguna paling aktif. Memberikan wawasan berharga untuk pengembangan lebih lanjut.

**Penting:** Modul ini memerlukan instance database.
**Inisialisasi:**
`analytics = client.ns.analytics.manager(database=db_instance)`

**Metode Utama:**
- `@analytics.track_usage`: Decorator yang ditambahkan ke *handler* untuk secara otomatis mencatat penggunaannya.
- `get_top_commands(limit=10)`: Mengambil daftar perintah yang paling sering digunakan.
- `get_active_users(limit=10)`: Mengambil daftar pengguna paling aktif.

**Contoh Penggunaan:**
```python
# Inisialisasi (asumsikan 'db' sudah ada)
# db = client.ns.data.db(storage_type="sqlite")
# analytics = client.ns.analytics.manager(database=db)
# ADMIN_ID = 123456789

# Tambahkan decorator ke handler yang ingin dilacak
@app.on_message(filters.command("ytdl"))
@analytics.track_usage
async def download_media(client, message):
    # ... (logika download media)
    await message.reply("Download selesai.")

# Handler untuk admin melihat statistik
@app.on_message(filters.command("botstats") & filters.user(ADMIN_ID))
async def show_bot_stats(client, message):
    top_cmds = await analytics.get_top_commands(limit=5)
    
    fmt = client.ns.telegram.formatter(mode="html")
    fmt.bold("📊 Statistik Perintah Teratas").new_line(2)
    if top_cmds:
        for cmd, count in top_cmds:
            fmt.mono(f"/{cmd}").text(f": {count} kali").new_line()
    else:
        fmt.text("Belum ada data.")
    
    await message.reply(fmt)

```
---
### `chat`
Menganalisis riwayat pesan dalam sebuah grup untuk memberikan wawasan statistik seperti pengguna paling aktif, kata yang sering digunakan, dan waktu puncak aktivitas.

**Inisialisasi:**
`analyzer = client.ns.analytics.chat()`

**Metode Utama:**
- `analyze(messages)`: Menerima daftar objek pesan Pyrogram dan mengembalikan objek `SimpleNamespace` dengan hasil analisis.

**Contoh Penggunaan:**
```python
# Handler untuk perintah .statschat di sebuah grup
# @app.on_message(filters.command("statschat", prefixes=".") & filters.me)
async def chat_stats_handler(client, message):
    status_msg = await message.edit("📈 Mengumpulkan pesan...")
    
    messages = []
    # Mengumpulkan hingga 1000 pesan terakhir dari riwayat chat
    async for msg in client.get_chat_history(message.chat.id, limit=1000):
        messages.append(msg)

    await status_msg.edit(f"⚙️ Menganalisis {len(messages)} pesan...")
    
    analyzer = client.ns.analytics.chat()
    stats = await analyzer.analyze(messages)
    
    fmt = client.ns.telegram.formatter(mode="html")
    fmt.bold(f"📊 Analisis untuk: {message.chat.title}").new_line(2)
    # ... (format output seperti top users, top words, etc.)
    await status_msg.edit(fmt)
```

</details>

<details>
<summary><strong>🔐 Autentikasi (`client.ns.auth`)</strong></summary>

### `manager`
Manajer peran pengguna untuk membatasi akses ke fitur-fitur tertentu dalam bot. Ini memungkinkan Anda membuat sistem hak akses (misal: admin, premium, user biasa) dengan mudah.

**Penting:** Modul ini memerlukan instance database.
**Inisialisasi:**
`auth = client.ns.auth(database=db_instance)`

**Metode Utama:**
- `set_role(user_id, role)`: Memberikan peran kepada pengguna.
- `remove_role(user_id, role)`: Menghapus peran dari pengguna.
- `get_roles(user_id)`: Mendapatkan daftar peran seorang pengguna.
- `@auth.requires_role("role_name")`: Decorator untuk membatasi akses handler.

**Contoh Penggunaan:**
```python
# Inisialisasi (asumsikan 'db' sudah ada)
# db = client.ns.data.db()
# auth = client.ns.auth(database=db)
# ADMIN_ID = 123456789

# Berikan peran admin kepada diri sendiri via perintah
@app.on_message(filters.command("getadmin") & filters.me)
async def grant_admin(client, message):
    await auth.set_role(message.from_user.id, "admin")
    await message.reply("Anda sekarang adalah admin.")

# Handler ini hanya bisa diakses oleh pengguna dengan peran "admin"
@app.on_message(filters.command("adminpanel"))
@auth.requires_role("admin")
async def admin_panel(client, message):
    await message.reply("Selamat datang di panel admin!")

# Handler ini memerlukan peran "premium"
@app.on_message(filters.command("premiumfeature"))
@auth.requires_role("premium")
async def premium_feature(client, message):
    await message.reply("Ini adalah fitur khusus premium.")
```

</details>

<details>
<summary><strong>🔒 Enkripsi (`client.ns.code`)</strong></summary>

### `encrypt`
Koleksi kelas untuk enkripsi dan dekripsi data.

**Inisialisasi:**
`cipher = client.ns.code.Cipher(key, method)`

| Parameter | Tipe Data | Default             | Deskripsi                                                 |
|-----------|-----------|---------------------|-----------------------------------------------------------|
| `key`     | `str`     | `"my_s3cr3t_k3y.."` | Kunci rahasia untuk enkripsi.                               |
| `method`  | `str`     | `"shift"`           | Metode enkripsi: `"bytes"` (rekomendasi), `"shift"`, `"binary"`. |

**Contoh Penggunaan:**
```python
cipher = client.ns.code.Cipher(key="kunci-rahasia-saya-123", method="bytes")
data_asli = {"user_id": 123, "plan": "premium", "active": True}

terenkripsi_hex = cipher.encrypt(data_asli)
print("Terenskripsi:", terenkripsi_hex)

didekripsi_kembali = cipher.decrypt(terenkripsi_hex)
print("Didekripsi:", didekripsi_kembali)
# Output: {'user_id': 123, 'plan': 'premium', 'active': True}
```

</details>

<details>
<summary><strong>📦 Data (`client.ns.data`)</strong></summary>

### `database`
Sistem database fleksibel yang mendukung penyimpanan lokal (JSON), SQLite, dan MongoDB, dengan enkripsi data otomatis.

**Inisialisasi:**
`db = client.ns.data.db(**options)`

| Parameter                 | Tipe Data      | Default                    | Deskripsi                                                     |
|---------------------------|----------------|----------------------------|---------------------------------------------------------------|
| `storage_type`            | `str`          | `"local"`                  | Tipe penyimpanan: `"local"`, `"sqlite"`, atau `"mongo"`.          |
| `file_name`               | `str`          | `"database"`               | Nama file untuk `.json` atau `.db`. Juga nama DB untuk Mongo. |
| `keys_encrypt`            | `str`          | `"default_db_key_12345"`   | Kunci rahasia untuk enkripsi data. **Ganti dengan kunci Anda!**   |
| `mongo_url`               | `str`          | `None`                     | URL koneksi MongoDB (wajib jika `storage_type="mongo"`).    |
| `auto_backup`             | `bool`         | `False`                    | Aktifkan backup otomatis ke Telegram? (Hanya untuk `local`/`sqlite`).|
| `backup_bot_token`        | `str`          | `None`                     | Token bot Telegram untuk mengirim file backup.                  |
| `backup_chat_id`          | `str` atau `int` | `None`                   | Chat ID tujuan untuk backup.                                    |
| `backup_interval_hours`   | `int`          | `24`                       | Interval backup dalam jam.                                    |

**Contoh Inisialisasi Lanjutan:**
```python
db_secure = client.ns.data.db(
    storage_type="sqlite",
    file_name="my_secure_bot_db",
    keys_encrypt="KUNCI_RAHASIA_SUPER_AMAN_SAYA",
    auto_backup=True,
    backup_bot_token="TOKEN_BOT_BACKUP_SAYA",
    backup_chat_id=-100123456789
)
```

**Operasi Data Dasar (CRUD):**
- `setVars(user_id, key, value)`: Menyimpan data.
- `getVars(user_id, key)`: Mengambil data.
- `removeVars(user_id, key)`: Menghapus data.
- `setListVars(user_id, key, value)`: Menambahkan item ke dalam sebuah list.
- `getListVars(user_id, key)`: Mengambil seluruh list.
- `removeListVars(user_id, key, value)`: Menghapus item spesifik dari list.

---
### `storekey`
Manajer untuk menangani kunci rahasia dari argumen terminal, mencegah *hardcoding*.

**Cara Menjalankan di Terminal:**
```bash
python3 main.py --key kunci-rahasia-anda --env config.env
```

**Contoh Kode di Python:**
```python
# Di dalam file main.py Anda
# key_manager = client.ns.data.key()
# SECRET_KEY, ENV_FILE = key_manager.handle_arguments()
# print(f"Kunci yang digunakan: {SECRET_KEY}")
# print(f"File env yang dimuat: {ENV_FILE}")
```
---
### `yaml`
Utilitas praktis untuk membaca file `.yml` dan mengubahnya menjadi objek Python yang bisa diakses dengan notasi titik (`.`).

**Contoh file `config.yml`:**
```yaml
app:
  name: MyAwesomeBot
  version: 1.0

database:
  host: localhost
  port: 27017
```

**Contoh Kode Python:**
```python
config = client.ns.data.yaml.loadAndConvert("config.yml")
if config:
    print(f"Nama Aplikasi: {config.app.name}")
    print(f"Host Database: {config.database.host}")
```

</details>

<details>
<summary><strong>💳 Pembayaran (`client.ns.payment`)</strong></summary>

### `payment`
Klien terintegrasi untuk berbagai payment gateway populer di Indonesia, memudahkan Anda menerima pembayaran di dalam bot atau aplikasi.

---
#### **Contoh Midtrans**
Gateway pembayaran yang sangat populer dan stabil.

**Inisialisasi:**
`midtrans = client.ns.payment.Midtrans(server_key, client_key, **kwargs)`

| Parameter      | Tipe Data | Default                                | Deskripsi                                                       |
|----------------|-----------|----------------------------------------|-----------------------------------------------------------------|
| `server_key`   | `str`     | -                                      | **Wajib.** Kunci Server Midtrans Anda (dari dashboard).           |
| `client_key`   | `str`     | -                                      | **Wajib.** Kunci Klien Midtrans Anda.                           |
| `is_production`| `bool`    | `True`                                 | Atur ke `False` untuk menggunakan mode Sandbox (pengembangan). |
| `callback_url` | `str`     | `"https://.../payment"`                | URL tujuan setelah pelanggan menyelesaikan pembayaran.          |

**Metode Utama:**
- `create_payment(order_id, gross_amount)`: Membuat sesi pembayaran baru.
- `check_transaction(order_id)`: Memeriksa status transaksi yang ada.

**Contoh Penggunaan:**
```python
# Inisialisasi untuk mode Sandbox
midtrans = client.ns.payment.Midtrans(
    server_key="SB-SERVER-KEY-ANDA", 
    client_key="SB-CLIENT-KEY-ANDA", 
    is_production=False
)

# Membuat pembayaran
try:
    payment_info = midtrans.create_payment(
        order_id="INV-USER123-002", 
        gross_amount=50000
    )
    # Anda bisa mengirim URL ini ke pengguna
    print("URL Pembayaran:", payment_info.redirect_url)
except Exception as e:
    print(f"Gagal membuat pembayaran: {e}")
```

---
#### **Contoh Tripay**
Alternatif payment gateway dengan banyak pilihan channel pembayaran.

**Inisialisasi:**
`tripay = client.ns.payment.Tripay(api_key)`

| Parameter | Tipe Data | Default | Deskripsi                            |
|-----------|-----------|---------|--------------------------------------|
| `api_key` | `str`     | -       | **Wajib.** Kunci API Tripay Anda.      |

**Metode Utama:**
- `create_payment(method, amount, order_id, customer_name)`: Membuat transaksi baru.
- `check_transaction(reference)`: Memeriksa status transaksi berdasarkan referensi.

**Contoh Penggunaan:**
```python
# Inisialisasi (ganti dengan kredensial Anda)
TRIPAY_API_KEY = "TRIPAY_API_KEY_ANDA"
tripay = client.ns.payment.Tripay(api_key=TRIPAY_API_KEY)

# Membuat pembayaran (contoh QRIS)
try:
    payment_info = tripay.create_payment(
        method="QRIS",           # Kode channel pembayaran (lihat dok. Tripay)
        amount=10000,
        order_id="INV-USER123-003",
        customer_name="Budi Santoso"
    )
    print("URL QRIS:", payment_info.data.qr_url)
    print("Reference untuk pengecekan:", payment_info.data.reference)
except Exception as e:
    print(f"Gagal membuat pembayaran Tripay: {e}")
```
---
#### **Contoh VioletMediaPay**
Gateway pembayaran lain yang menyediakan metode pembayaran umum. Perhatikan bahwa metode pada kelas ini bersifat `async`.

**Inisialisasi:**
`violet = client.ns.payment.Violet(api_key, secret_key, live=False)`

| Parameter    | Tipe Data | Default | Deskripsi                                             |
|--------------|-----------|---------|-------------------------------------------------------|
| `api_key`    | `str`     | -       | **Wajib.** Kunci API VioletMediaPay Anda.             |
| `secret_key` | `str`     | -       | **Wajib.** Kunci Rahasia VioletMediaPay Anda.         |
| `live`       | `bool`    | `False` | Atur ke `True` untuk beralih ke mode produksi/live.   |

**Metode Utama (Asinkron):**
- `create_payment(channel_payment, amount, **kwargs)`: Membuat pembayaran.
- `check_transaction(ref, ref_id)`: Memeriksa status pembayaran.

**Contoh Penggunaan (dalam fungsi `async`):**
```python
import asyncio

async def buat_pembayaran_violet(client):
    VIOLET_API_KEY = "VIOLET_API_KEY_ANDA"
    VIOLET_SECRET_KEY = "VIOLET_SECRET_KEY_ANDA"
    
    violet = client.ns.payment.Violet(
        api_key=VIOLET_API_KEY,
        secret_key=VIOLET_SECRET_KEY,
        live=False  # Mode Sandbox
    )

    try:
        # Membuat pembayaran
        payment_info = await violet.create_payment(
            channel_payment="QRISC",  # Contoh: QRIS Cepat
            amount="15000",
            produk="Donasi untuk Bot Keren"
        )

        if payment_info.success:
            print("URL QR:", payment_info.data.qrcode)
            print("Reference ID:", payment_info.data.ref_kode)
            print("Reference Kode:", payment_info.data.id_reference)

            # Simpan ref dan ref_id untuk pengecekan nanti
            ref_kode = payment_info.data.ref_kode 
            ref_id = payment_info.data.id_reference
            
            # Menunggu sebentar sebelum cek status
            await asyncio.sleep(10)
            
            # Memeriksa status transaksi
            status_info = await violet.check_transaction(ref=ref_kode, ref_id=ref_id)
            if status_info.success:
                print(f"Status Pembayaran [{ref_kode}]: {status_info.data.status}")
        else:
            print("Gagal membuat pembayaran:", payment_info.msg)
            
    except Exception as e:
        print(f"Terjadi kesalahan saat proses pembayaran: {e}")

# Untuk menjalankan contoh ini (di luar event handler Pyrogram):
# asyncio.run(buat_pembayaran_violet(client))
```

</details>

<details>
<summary><strong>🗓️ Penjadwalan (`client.ns.schedule`)</strong></summary>

### `scheduler`
Modul untuk menjalankan tugas-tugas secara otomatis pada waktu atau interval tertentu, menggunakan sintaks cron. Sangat berguna untuk laporan harian, pembersihan data, pengiriman pengingat, dll.

**Penting:** Fitur ini memerlukan dependensi `aiocron`. Instal dengan "extra" `[schedule]`.
**Inisialisasi:**
`scheduler = client.ns.schedule`
(Instance sudah siap pakai, tidak perlu inisialisasi manual).

**Metode Utama:**
- `@scheduler.cron("cron_expression")`: Decorator untuk mendaftarkan fungsi asinkron agar berjalan sesuai jadwal.
- `scheduler.start()`: Memulai *event loop* penjadwal. Panggil ini sekali di akhir skrip Anda, sebelum `app.run()`.

**Contoh Penggunaan:**
```python
# scheduler = client.ns.schedule

# Fungsi ini akan dijalankan setiap hari pada pukul 08:00
@scheduler.cron("0 8 * * *")
async def send_daily_server_status():
    client.ns.utils.log.info("Menjalankan tugas laporan server harian...")
    stats = client.ns.server.monitor.get_stats()
    report = (
        f"☀️ **Laporan Server Pagi**\n"
        f"▫️ CPU: `{stats.cpu_percent}%`\n"
        f"▫️ RAM: `{stats.ram_percent}%`"
    )
    # Kirim ke channel log
    # await client.send_message(LOG_CHANNEL_ID, report)

# Di bagian bawah file utama Anda
# async def main():
#     ...
#     scheduler.start() # Aktifkan penjadwal
#     await client.start()
#     await pyrogram.idle()
#     await client.stop()

# loop.run_until_complete(main())
```

</details>


<details>
<summary><strong>🖥️ Server (`client.ns.server`)</strong></summary>

### `monitor`
Utilitas untuk memantau penggunaan sumber daya server Linux.

**Contoh Penggunaan:**
```python
stats = client.ns.server.monitor.get_stats()
pesan_status = (
    f"🖥️ **Status Server**\n"
    f"▫️ CPU: `{stats.cpu_percent}%`\n"
    f"▫️ RAM: `{stats.ram_used_gb:.2f}/{stats.ram_total_gb:.2f} GB ({stats.ram_percent}%)`\n"
    f"▫️ Disk: `{stats.disk_used_gb:.2f}/{stats.disk_total_gb:.2f} GB ({stats.disk_percent}%)`"
)
# await message.reply(pesan_status)
```
---
### `process`
Manajer untuk melihat dan mengelola proses yang berjalan di server Linux.

**Metode Utama:**
- `list(limit=10, sort_by='cpu_percent')`: Mendapatkan daftar proses.
- `kill(pid)`: Menghentikan proses berdasarkan PID.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("top"))
async def top_processes(client, message):
    try:
        top_procs = await client.ns.server.process.list(limit=5, sort_by='memory_percent')
        
        fmt = client.ns.telegram.formatter(mode="html")
        fmt.bold("🔥 Top 5 Proses Berdasarkan Memori").new_line(2)
        
        for p in top_procs:
            fmt.mono(f"PID: {p.pid:<5}").text(f" | RAM: {p.memory_percent:.2f}% | ").bold(p.name).new_line()
        
        await message.reply(fmt)
    except Exception as e:
        await message.reply(f"Gagal mengambil daftar proses: {e}")
```
---
### `speedtest`
Menjalankan tes kecepatan internet (download, upload, ping) langsung dari server.

**Penting:** Fitur ini memerlukan dependensi `speedtest-cli`. Instal dengan "extra" `[server]`.

**Inisialisasi:**
`speedtester = client.ns.server.speedtest` (sudah siap pakai)

**Metode Utama:**
- `run()`: Menjalankan tes dan mengembalikan gambar hasil (`BytesIO`).

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("speedtest", prefixes=".") & filters.me)
# async def run_speedtest(client, message):
#     status = await message.edit("🚀 Menjalankan tes kecepatan...")
#     try:
#         result_image = await client.ns.server.speedtest.run()
#         await client.send_photo(message.chat.id, photo=result_image, caption="✅ Tes selesai.")
#         await status.delete()
#     except Exception as e:
#         await status.edit(f"❌ Gagal: {e}")
```
---
### `user`
Kelas untuk mengelola pengguna SSH di server Linux dari jarak jauh. Berguna untuk membuat atau menghapus akses pengguna secara dinamis.

**Inisialisasi:**
`user_manager = client.ns.server.user(bot_token, chat_id)`

| Parameter   | Tipe Data | Default                                    | Deskripsi                                             |
|-------------|-----------|--------------------------------------------|-------------------------------------------------------|
| `bot_token` | `str`     | `"74196...VWICA"` (Contoh)                 | Token bot Telegram untuk mengirim detail login.         |
| `chat_id`   | `int`     | `1964437366` (Contoh)                      | Chat ID tujuan untuk mengirim pesan.                    |

**Metode Utama:**
- `add_user(ssh_username=None, ssh_password=None)`: Menambah pengguna baru. Jika parameter kosong, akan dibuat secara acak.
- `delete_user(ssh_username)`: Menghapus pengguna.

**Catatan Penting:** Skrip ini memerlukan hak akses `sudo` tanpa password untuk menjalankan perintah `adduser` dan `deluser` di server.

</details>

<details>
<summary><strong>✈️ Telegram (`client.ns.telegram`)</strong></summary>

### `actions`
Modul untuk menampilkan status *chat action* (misal: "typing...", "uploading photo...") secara otomatis selama sebuah proses berjalan.

**Metode yang Tersedia:**
- `typing(chat_id)`
- `upload_photo(chat_id)`
- `upload_video(chat_id)`
- `record_video(chat_id)`
- `record_voice(chat_id)`

**Contoh Penggunaan:**
```python
import asyncio

# @app.on_message(...)
async def long_process_handler(client, message):
    # Bot akan menampilkan "typing..." selama proses di dalam blok 'with'
    async with client.ns.telegram.actions.typing(message.chat.id):
        await asyncio.sleep(5)  # Simulasi tugas yang panjang
        await message.reply("Selesai!")
```
---
### `argument`
Toolkit untuk mem-parsing dan mengekstrak informasi dari objek `message` Pyrogram dengan mudah. Kini lebih andal untuk menangani ID pengguna, username, maupun balasan.

**Metode Utama:**
- `getMessage(message, is_arg=False)`: Mengambil teks dari pesan balasan atau dari argumen perintah.
- `getReasonAndId(message, sender_chat=False)`: Mengekstrak `user_id` dan `alasan` dari pesan.

**Contoh Penggunaan (`getReasonAndId`):**
```python
@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
    if not user_id:
        return await message.reply("Sintaks tidak valid.")

    print(f"User yang akan diban: {user_id}")
    print(f"Alasan: {reason or 'Tidak ada alasan'}")
```
---
### `button`
Perkakas canggih untuk membuat `InlineKeyboardMarkup` dan `ReplyKeyboardMarkup`.

#### `create_inline_keyboard(text, cb_prefix=None)`
Membuat keyboard inline dari sintaks teks sederhana.
- **Sintaks:** `| Label Tombol - callback_data |` atau `| Label Tombol - https://url.com |`
- **Parameter Tambahan (opsional):** Tambahkan `;same`, `;copy`, atau `;user` setelah callback data.
- **`cb_prefix` (str):** Jika diberikan, semua `callback_data` akan secara otomatis diawali dengan `cb_prefix_`. Berguna untuk membuat sistem menu yang terstruktur.

**Contoh `create_inline_keyboard`:**
```python
teks_inline = """
Pilih salah satu menu di bawah:
| 👤 Profil - profil_user |
| 💰 Donasi - donasi;same |
| 🌐 Website Kami - https://github.com/SenpaiSeeker/norsodikin |
| 📋 Salin ID Saya - 12345678;copy |
"""
keyboard, sisa_teks = client.ns.telegram.button.create_inline_keyboard(teks_inline)
await message.reply(sisa_teks, reply_markup=keyboard)
```

#### `create_button_keyboard(text)`
Membuat keyboard balasan (tombol di bawah area input teks).
- **Sintaks:** `| Label Tombol |`
- **Parameter Tambahan (opsional):** `| Label;is_contact |` atau `| Label;same |`.

**Contoh `create_button_keyboard`:**
```python
teks_reply = """
Halo! Apa yang bisa saya bantu?
| 📑 Daftar Produk |
| 📞 Hubungi CS;is_contact |
| ❓ Bantuan;same |
"""
keyboard, sisa_teks = client.ns.telegram.button.create_button_keyboard(teks_reply)
await message.reply(sisa_teks, reply_markup=keyboard)
```

#### `build_button_grid(buttons, row_inline=None, row_width=2)`
Membuat keyboard inline dari daftar dictionary secara terprogram.

**Contoh `build_button_grid`:**
```python
button_list = [
    {"text": "Apple", "callback_data": "fruit_apple"},
    {"text": "Orange", "callback_data": "fruit_orange"},
    {"text": "Grape", "callback_data": "fruit_grape"}
]
footer_button = [{"text": "« Kembali", "callback_data": "back_to_main"}]

keyboard = client.ns.telegram.button.build_button_grid(
    buttons=button_list,
    row_inline=footer_button,
    row_width=2  # 2 tombol per baris
)
await message.reply("Pilih buah:", reply_markup=keyboard)
```

#### `create_pagination_keyboard(...)`
Membuat keyboard paginasi yang dinamis untuk menampilkan daftar item.

| Parameter              | Tipe Data      | Deskripsi                                                        |
|------------------------|----------------|------------------------------------------------------------------|
| `items`                | `list`         | Daftar item yang akan ditampilkan (bisa `str` atau `dict`).        |
| `current_page`         | `int`          | Halaman yang sedang aktif.                                         |
| `items_per_page`       | `int`          | Jumlah item per halaman.                                           |
| `callback_prefix`      | `str`          | Prefix untuk callback data tombol navigasi (misal: "nav_2").        |
| `item_callback_prefix` | `str`          | Prefix untuk callback data setiap item.                            |
| `extra_params`         | `list` (opt)   | Tombol tambahan di bagian bawah (misal: tombol kembali).         |

**Contoh `create_pagination_keyboard`:**
```python
# Asumsikan 'products' adalah daftar item dari database
products = [f"Produk {i}" for i in range(1, 21)]

# Handler untuk perintah awal
@app.on_message(filters.command("produk"))
async def show_products(client, message):
    keyboard = client.ns.telegram.button.create_pagination_keyboard(
        items=products,
        current_page=1,
        items_per_page=5,
        callback_prefix="produk_page",
        item_callback_prefix="pilih_produk"
    )
    await message.reply("Daftar Produk (Halaman 1/4):", reply_markup=keyboard)

# Handler untuk callback navigasi
@app.on_callback_query(filters.regex(r"^produk_page_"))
async def change_page(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    keyboard = client.ns.telegram.button.create_pagination_keyboard(
        items=products,
        current_page=page,
        items_per_page=5,
        callback_prefix="produk_page",
        item_callback_prefix="pilih_produk"
    )
    total_pages = (len(products) + 4) // 5
    await callback_query.message.edit_text(
        f"Daftar Produk (Halaman {page}/{total_pages}):",
        reply_markup=keyboard
    )
```
---
### `copier`
Modul canggih untuk menyalin pesan dari link Telegram. Mendukung penyalinan tunggal, ganda, dan rentang, dengan penanganan `FloodWait` otomatis dan metode canggih untuk menangani link channel/grup privat secara andal. Media akan diunduh dan dikirim ulang lengkap dengan metadata.

**Metode Utama:**
`copy_from_links(user_chat_id, links_text, status_message)`

**Contoh Penggunaan Lengkap:**
```python
COPY_HELP_TEXT = """
**Fitur Penyalin Pesan**
Saya bisa menyalin pesan dari channel/grup mana pun, cukup berikan linknya.
• **Satu Pesan**: `/copy <link>`
• **Beberapa Pesan**: `/copy <link1> <link2>`
• **Rentang Pesan**: `/copy <link_awal> | <link_akhir>`
"""
@app.on_message(filters.command("copy"))
async def copy_message_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text(COPY_HELP_TEXT, quote=True)
    links_text = message.text.split(None, 1)[1]
    status_msg = await message.reply_text("⏳ `Memvalidasi link...`", quote=True)
    try:
        await client.ns.telegram.copier.copy_from_links(
            user_chat_id=message.chat.id,
            links_text=links_text,
            status_message=status_msg
        )
    except ValueError as ve:
        await status_msg.edit(f"❌ **Error:** {ve}")
    except Exception as e:
        client.ns.utils.log.error(f"Copy Handler Error: {e}")
        await status_msg.edit(f"❌ **Terjadi kesalahan tak terduga:**\n`{e}`")
```
---
### `errors.handle`
Decorator untuk menangani error di *handler* secara otomatis. Mencegah bot crash dan menyediakan logging yang detail serta pesan yang ramah untuk pengguna.

**Parameter Decorator:**
| Parameter | Tipe Data | Deskripsi |
|---|---|---|
| `log_channel_id` | `int` | ID channel (atau chat) untuk mengirim log traceback lengkap. |
| `error_message_template`| `str` | Template pesan yang akan dikirim ke pengguna jika terjadi error. |
| `silent`|`bool`| Jika `True`, tidak akan mengirim pesan balasan ke pengguna. |

**Contoh Penggunaan:**
```python
LOG_CHANNEL = -1001234567890

# Handler tanpa penanganan error manual
# @app.on_message(filters.command("divide"))
# async def divide_by_zero(client, message):
#     await message.reply(1 / 0)

# Handler yang sama, tapi sekarang aman dan informatif
@app.on_message(filters.command("divide"))
@client.ns.telegram.errors.handle(log_channel_id=LOG_CHANNEL)
async def divide_by_zero_safe(client, message):
    await message.reply(1 / 0)

# Jika terjadi error, decorator akan:
# 1. Menangkap ZeroDivisionError.
# 2. Mengirim traceback lengkap ke LOG_CHANNEL.
# 3. Membalas pesan pengguna dengan: "❌ Terjadi kesalahan:\n`ZeroDivisionError: division by zero`"
```
---
### `formatter`
Builder canggih untuk menyusun pesan berformat dengan sintaks yang fasih. **Pembaruan Penting:** Objek `formatter` kini berfungsi persis seperti string Python biasa (`str`), sehingga Anda **tidak perlu lagi memanggil `.to_string()`** di akhir. Ini membuat integrasi dengan fungsi Pyrogram seperti `message.reply()` menjadi mulus.

**Inisialisasi:**
`fmt = client.ns.telegram.formatter(mode="html")`

**Contoh Penggunaan:**
```python
fmt = client.ns.telegram.formatter(mode="html")

pesan = (
    fmt.bold("🔥 Update Sistem").new_line(2)
    .text("Layanan telah kembali normal.").new_line()
    .italic("Terima kasih atas kesabaran Anda.")
)

# 'pesan' sekarang adalah objek string yang bisa langsung digunakan:
# await message.reply(pesan)
```
### `story`
Modul untuk mengunduh semua story aktif dari seorang pengguna berdasarkan username mereka.

> **⚠️ PERINGATAN PENTING:** Fitur ini **HANYA BERFUNGSI JIKA DIGUNAKAN DI USERBOT** (akun pengguna). Bot API standar tidak memiliki izin untuk melihat atau mengunduh story. Mencoba menjalankan ini dengan akun bot akan menghasilkan error.

**Metode Utama:**
`download_user_stories(username, chat_id, status_message)`

| Parameter        | Tipe Data                  | Deskripsi                                             |
|------------------|----------------------------|-------------------------------------------------------|
| `username`       | `str`                      | Username target (misal: `"@telegram"`).                |
| `chat_id`        | `int`                      | ID chat ke mana hasil story akan dikirim.             |
| `status_message` | `pyrogram.types.Message`   | Pesan yang akan diedit untuk menampilkan status proses. |

**Contoh Penggunaan pada Userbot:**
```python
# Contoh handler untuk perintah .getstory
@app.on_message(filters.command("getstory", prefixes=".") & filters.me)
async def get_user_stories_handler(client, message):
    if len(message.command) < 2:
        return await message.edit_text("Sintaks: `.getstory @username`")

    username = message.command[1]
    # Mengedit pesan perintah itu sendiri sebagai pesan status
    status_msg = await message.edit_text(f"Memulai proses untuk `{username}`...")

    try:
        await client.ns.telegram.story.download_user_stories(
            username=username,
            chat_id=message.chat.id,
            status_message=status_msg  # Menggunakan pesan yang sama untuk update
        )
        # Jika berhasil, pesan status akan terhapus oleh fungsi itu sendiri
        # Kita bisa menghapus pesan perintah awal jika mau
        if status_msg.id != message.id:
            await message.delete()

    except Exception as e:
        # Menangani error (misal: dijalankan di bot biasa)
        await status_msg.edit_text(f"❌ **Error Kritis:** {e}")
```
### `videofx` -> `client.ns.telegram.videofx`
Modul canggih untuk manipulasi video, seperti membuat **animasi teks dinamis** atau mengubah video biasa menjadi stiker video `.webm` atau GIF.

#### **Metode Utama: `text_to_video()`**
Mengubah satu atau beberapa baris teks menjadi file video animasi `.mp4`.

| Parameter       | Tipe Data | Default  | Deskripsi                                                                 |
|-----------------|-----------|----------|---------------------------------------------------------------------------|
| `text`          | `str`     | -        | Teks yang akan dianimasikan. Gunakan `;` untuk membuat baris baru.         |
| `output_path`   | `str`     | -        | Path file tujuan untuk menyimpan video (misal: `"hasil.mp4"`).              |
| `duration`      | `float`   | `5.0`    | Durasi video dalam detik.                                                 |

#### **Metode Utama: `video_to_sticker()`**
Mengonversi file video menjadi stiker video `.webm` dengan resolusi 512px yang sesuai standar Telegram.

| Parameter   | Tipe Data | Default  | Deskripsi                                                        |
|-------------|-----------|----------|------------------------------------------------------------------|
| `video_path`  | `str`     | -        | Path file video sumber yang akan dikonversi.                       |
| `output_path` | `str`     | -        | Path file tujuan untuk stiker `.webm`.                            |

#### **Metode Utama: `video_to_gif()`**
Mengonversi file video menjadi file animasi GIF.

| Parameter   | Tipe Data | Deskripsi                                  |
|-------------|-----------|--------------------------------------------|
| `video_path`  | `str`     | Path file video sumber yang akan dikonversi. |
| `output_path` | `str`     | Path file tujuan untuk GIF `.gif`.          |


---
#### **Contoh Penggunaan (Animasi Teks Dinamis):**

```python
import os
import uuid

# Contoh Handler untuk perintah /animatetext
@app.on_message(filters.command("animatetext"))
async def animated_sticker_handler(client, message):
    text_input = client.ns.telegram.arg.getMessage(message, is_arg=True)
    if not text_input:
        return await message.reply("Gunakan: `/animatetext Teks Anda;Baris baru`")

    status_msg = await message.reply("🎨 Menciptakan animasi teks...")

    async with client.ns.utils.files.temp_dir() as tmpdir:
        video_path = os.path.join(tmpdir, f"{uuid.uuid4()}.mp4")
        sticker_path = os.path.join(tmpdir, f"{uuid.uuid4()}.webm")
        try:
            await client.ns.telegram.videofx.text_to_video(text=text_input, output_path=video_path)
            await status_msg.edit("✨ Mengonversi video menjadi stiker...")
            await client.ns.telegram.videofx.video_to_sticker(video_path=video_path, output_path=sticker_path)
            await client.send_sticker(message.chat.id, sticker_path)
            await status_msg.delete()
        except Exception as e:
            await status_msg.edit(f"❌ Terjadi kesalahan: {e}")
```

</details>

<details>
<summary><strong>🛠️ Utilitas (`client.ns.utils`)</strong></summary>

### `audiofx`
Modul untuk menerapkan berbagai efek audio pada file suara, seperti pesan suara.

**Inisialisasi:** `audio_fx = client.ns.utils.audiofx` (sudah siap pakai)

**Metode Utama:** `apply_effect(input_path, output_path, effect)`

**Efek yang Tersedia:** `chipmunk`, `robot`, `echo`, `reverse`.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("voicefx", prefixes=".") & filters.reply)
# async def voice_effect(client, message):
#     if not message.reply_to_message.voice:
#         return await message.edit("Balas ke pesan suara.")
#
#     effect_name = message.command[1]
#     status = await message.edit(f"🎤 Menerapkan efek {effect_name}...")
#
#     async with client.ns.utils.files.temp_dir() as tmpdir:
#         input_audio = await client.download_media(message.reply_to_message.voice)
#         output_audio = os.path.join(tmpdir, "output.ogg")
#
#         await client.ns.utils.audiofx.apply_effect(input_audio, output_audio, effect_name)
#         await client.send_voice(message.chat.id, voice=output_audio)
#         await status.delete()
```
---
### `cache`
Decorator untuk menyimpan hasil dari sebuah fungsi ke dalam memori (*caching*) untuk jangka waktu tertentu. Sangat berguna untuk mempercepat respon dan mengurangi beban pada API eksternal.

**Metode:** `@client.ns.utils.cache(ttl=seconds)`

---
### `carbon`
Menghasilkan gambar potongan kode yang indah (seperti `carbon.now.sh`) secara terprogram.

**Inisialisasi:** `carbon = client.ns.utils.carbon()`
**Metode Utama:** `generate(code)`
**Contoh:**
```python
# @app.on_message(filters.command("carbon") & filters.reply)
# async def carbon_handler(client, message):
#     code = message.reply_to_message.text
#     image_bytes = await client.ns.utils.carbon().generate(code)
#     # await message.reply_photo(BytesIO(image_bytes))
```
---
### `downloader`
Utilitas untuk mengunduh video atau audio dari berbagai platform (YouTube, dll) menggunakan `yt-dlp`, kini dengan penanganan *geo-restriction* otomatis untuk YouTube.

**Inisialisasi:** `downloader = client.ns.utils.downloader(cookies_file_path=None, download_path="downloads")`

**Metode Utama:**
- `download(url, audio_only=False, progress_callback=None)`
- `search_youtube(query, limit=5)`: Mencari video di YouTube dan mengembalikan daftar hasil.

---
### `faker`
Generator data pribadi palsu untuk berbagai keperluan, seperti testing atau privasi.

**Inisialisasi:** `faker = client.ns.utils.faker` (sudah siap pakai)

**Metode Utama:** `generate()`: Mengembalikan objek `SimpleNamespace` dengan atribut seperti `name`, `address`, `email`, `job`, `phone_number`, dll.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("fakeinfo", prefixes="."))
# async def fake_info(client, message):
#     info = client.ns.utils.faker.generate()
#     response = (
#         f"**Nama:** {info.name}\n"
#         f"**Alamat:** {info.address.replace('\n', ', ')}\n"
#         f"**Email:** `{info.email}`"
#     )
#     await message.edit(response)
```
---
### `files`
Manajer file yang aman untuk menangani file dan direktori temporer. Menjamin pembersihan otomatis setelah selesai digunakan, bahkan jika terjadi error.

**Metode Utama:** `async with client.ns.utils.files.temp_dir() as tmpdir:`

---
### `github`
Mengambil informasi profil pengguna dari GitHub menggunakan API resmi untuk data yang andal dan akurat.

**Inisialisasi:** `gh = client.ns.utils.github()`
**Metode Utama:** `get_user_info(username)`
**Contoh:**
```python
# @app.on_message(filters.command("github"))
# async def github_lookup(client, message):
#     username = message.command[1]
#     info = await client.ns.utils.github().get_user_info(username)
#     await message.reply(f"Nama: {info.name}\nBio: {info.bio}")
```
---
### `gofile`
Utilitas untuk mengunggah file ke layanan hosting GoFile.io dan mendapatkan tautan unduhan.

**Inisialisasi:** `uploader = client.ns.utils.gofile` (sudah siap pakai)

**Metode Utama:** `upload(file_path)`: Mengunggah file dan mengembalikan objek `SimpleNamespace` dengan detail seperti `downloadPage`, `name`, dll.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("gofile", prefixes=".") & filters.reply)
# async def upload_to_gofile(client, message):
#     if not message.reply_to_message.media:
#         return await message.edit("Balas ke file.")
#
#     status = await message.edit("📥 Mengunduh...")
#     file_path = await client.download_media(message.reply_to_message)
#
#     await status.edit("📤 Mengunggah ke GoFile...")
#     result = await client.ns.utils.gofile.upload(file_path)
#     await status.edit(f"**Tautan Unduhan:** {result.downloadPage}")
#     os.remove(file_path)
```
---
### `grad`
Mempercantik output terminal dengan teks bergradien dan timer countdown.

**Metode Utama:** `render_text(text)`, `countdown(seconds)`, `ping()`

---
### `image`
Kumpulan alat untuk memanipulasi gambar.
**Metode Utama:**
- `add_watermark(image_bytes, text)`
- `resize(image_bytes, size)`
- `convert_format(image_bytes, output_format="PNG")`
- `create_meme(image_bytes, top_text, bottom_text)`
- `apply_filter(image_bytes, filter_name)`
- `remove_background(image_bytes)`
- `convert_sticker_to_png(sticker_bytes)`
- `deepfry(image_bytes)`
- `create_afk_card(pfp_bytes, name, reason, duration)`

---
### `log`
Logger canggih pengganti `print()` yang memberikan output berwarna dan informatif ke konsol.

---
### `mediainfo`
Mengekstrak metadata teknis (codec, bitrate, resolusi, dll.) dari file video atau audio menggunakan `ffprobe`.

**Inisialisasi:** `inspector = client.ns.utils.mediainfo` (sudah siap pakai)

**Metode Utama:** `get_info(file_path)`: Menganalisis file dan mengembalikan objek `SimpleNamespace` dengan detail `video`, `audio`, dan `general`.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("mediainfo", prefixes=".") & filters.reply)
# async def get_media_info(client, message):
#     # ... (logika download file)
#     file_path = "path/to/video.mp4"
#     info = await client.ns.utils.mediainfo.get_info(file_path)
#     if info.video:
#         await message.edit(f"Resolusi: {info.video.resolution}")
```
---
### `osint`
Toolkit untuk melakukan investigasi sumber terbuka dasar.
**Inisialisasi:** `osint = client.ns.utils.osint()`
**Metode Utama:**
- `get_ip_info(ip_or_domain)`: Mengambil info geolokasi dan ISP.
- `check_username(username)`: Memeriksa ketersediaan username di berbagai platform.

---
### `paste`
Mengunggah teks panjang ke layanan pastebin (seperti spaceb.in) dan mengembalikan URL.
**Inisialisasi:** `paster = client.ns.utils.paste()`
**Metode Utama:** `paste(text)`
**Contoh:**
```python
# @app.on_message(filters.command("paste") & filters.reply)
# async def paste_handler(client, message):
#     url = await client.ns.utils.paste().paste(message.reply_to_message.text)
#     await message.reply(f"Teks Anda diunggah ke: {url}")
```
---
### `progress`
Callback helper untuk menampilkan progress bar dinamis saat mengunggah/mengunduh file dengan Pyrogram.

---
### `ratelimit`
Decorator untuk membatasi frekuensi penggunaan perintah oleh pengguna. Mencegah spam.
**Metode:** `@client.ns.utils.ratelimit(limit=1, per_seconds=60)`

---
### `shell`
Eksekutor perintah shell/terminal secara asinkron.

---
### `url`
Utilitas sederhana untuk memendekkan URL menggunakan layanan TinyURL.

---
### `wikipedia`
Mencari artikel di Wikipedia dan mengembalikan ringkasan, URL, dan gambar utama.
**Inisialisasi:** `wiki = client.ns.utils.wikipedia(lang="id")`
**Metode Utama:** `search(query, limit=1)`
**Contoh:**
```python
# @app.on_message(filters.command("wiki"))
# async def wiki_search(client, message):
#     query = message.command[1]
#     result = await client.ns.utils.wikipedia().search(query)
#     await message.reply_photo(result.image_url, caption=f"**{result.title}**\n{result.summary}")
```

</details>

<details>
<summary><strong>🗣️ Percakapan Interaktif (`client.listen()` & `chat.ask()`)</strong></summary>

### `listen`
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
        umur_msg = await nama_msg.chat.ask(f"OK, {nama_msg.text}. Berapa usiamu?")
        await message.reply(f"Terima kasih! Data tersimpan: Nama={nama_msg.text}, Usia={umur_msg.text}.")
    except asyncio.TimeoutError:
        await message.reply("Waktu habis. Silakan coba lagi.")
```

</details>

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk proyek komersial maupun non-komersial.

---

Semoga dokumentasi yang komprehensif ini membuat pengalaman pengembangan Anda menjadi lebih mudah dan menyenangkan. Selamat mencoba dan berkreasi dengan `norsodikin`! Jika ada pertanyaan atau butuh bantuan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
