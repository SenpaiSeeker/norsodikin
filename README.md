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
*   **Untuk semua fitur AI (TTS, Web Summarizer, Bing, Translate, QR Code, Vision, STT, Ollama):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[ai]"
    ```
    > **Catatan Penting untuk Pembaca QR Code:**
    > Fitur `qrcode.read()` memerlukan library `zbar`. Pada sistem berbasis Debian/Ubuntu, instal dengan:
    > `sudo apt-get install -y libzbar0`

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
*   **Instal Semua Fitur (Sakti Penuh):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[all]"
    ```

## Konsep Dasar & Integrasi Pyrogram

Keajaiban `norsodikin` terletak pada integrasi `monkey-patching` yang mulus dengan Pyrogram. Cukup dengan mengimpor `nsdev` sekali di skrip utama Anda, semua fungsionalitas akan otomatis "menempel" pada objek `client` Anda melalui namespace `ns`.

Semua modul dikelompokkan secara logis:
- `client.ns.ai`: Semua yang berhubungan dengan Kecerdasan Buatan.
- `client.ns.telegram`: Utilitas spesifik untuk Telegram (tombol, format teks, dll.).
- `client.ns.data`: Manajemen data (database, file config YAML).
- `client.ns.utils`: Perkakas umum (logger, downloader, shell).
- `client.ns.server`: Manajemen server Linux (proses, pengguna, monitor).
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
<summary><strong>📚 Referensi API Lengkap (Klik untuk Buka/Tutup)</strong></summary>

Berikut adalah panduan mendalam untuk setiap modul yang tersedia, lengkap dengan parameter dan contoh penggunaan.

### 1. `actions` -> `client.ns.telegram.actions`
Modul untuk menampilkan status *chat action* (misal: "typing...", "uploading photo...") secara otomatis selama sebuah proses berjalan. Ini memberikan feedback visual kepada pengguna.

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

### 2. `addUser` -> `client.ns.server.user`
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

---

### 3. `argument` -> `client.ns.telegram.arg`
Toolkit untuk mem-parsing dan mengekstrak informasi dari objek `message` Pyrogram dengan mudah.

**Metode Utama:**
- `getMessage(message, is_arg=False)`: Mengambil teks dari pesan balasan atau dari argumen perintah.
- `getReasonAndId(message, sender_chat=False)`: Mengekstrak `user_id` dan `alasan` dari pesan. Sangat berguna untuk perintah moderasi seperti `/ban` atau `/kick`.

**Contoh Penggunaan (`getReasonAndId`):**
```python
@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    # Kasus 1: /ban @username alasan...
    # Kasus 2: /ban (reply ke pesan) alasan...
    # Kasus 3: /ban 12345678
    user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
    if not user_id:
        await message.reply("Sintaks tidak valid. Balas pesan atau sebutkan user ID/username.")
        return

    print(f"User yang akan diban: {user_id}")
    print(f"Alasan: {reason or 'Tidak ada alasan'}")
```
---

### 4. `bing` -> `client.ns.ai.bing` (Tidak Stabil)
Generator gambar AI menggunakan Bing Image Creator. Karena ketergantungan pada *web scraping*, modul ini rentan terhadap perubahan dari sisi Bing.

**Inisialisasi:**
`bing_generator = client.ns.ai.bing(auth_cookie_u)`

| Parameter       | Tipe Data | Default | Deskripsi                                        |
|-----------------|-----------|---------|--------------------------------------------------|
| `auth_cookie_u` | `str`     | -       | **Wajib.** Nilai cookie `_U` dari akun Bing Anda. |

**Metode Utama:**
`generate(prompt, num_images=4)`

**Contoh Penggunaan:**
```python
BING_COOKIE = "NILAI_COOKIE__U_DARI_BING.COM"
try:
    bing_generator = client.ns.ai.bing(auth_cookie_u=BING_COOKIE)
    prompt = "kucing astronot di bulan, lukisan cat minyak"
    list_url = await bing_generator.generate(prompt)
    if list_url:
        await message.reply_photo(list_url[0], caption=prompt)
except Exception as e:
    await message.reply(f"Gagal membuat gambar: {e}")
```

---

### 5. `button` -> `client.ns.telegram.button`
Perkakas canggih untuk membuat `InlineKeyboardMarkup` dan `ReplyKeyboardMarkup`.

#### `create_inline_keyboard(text)`
Membuat keyboard inline dari sintaks teks sederhana.
- **Sintaks:** `| Label Tombol - callback_data |` atau `| Label Tombol - https://url.com |`
- **Parameter Tambahan (opsional):** Tambahkan `;same`, `;copy`, atau `;user` setelah callback data.
  - `;same`: Menempatkan tombol di baris yang sama dengan tombol sebelumnya.
  - `;copy`: Tombol akan menyalin teks (payload) ke clipboard.
  - `;user`: Tombol akan membuka chat dengan user ID (payload).

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
  - `;is_contact`: Meminta kontak pengguna.
  - `;same`: Tombol di baris yang sama.

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

### 6. `database` -> `client.ns.data.db`
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

### 7. `downloader` -> `client.ns.utils.downloader`
Utilitas untuk mengunduh video atau audio dari berbagai platform (YouTube, dll) menggunakan `yt-dlp`.

**Inisialisasi:**
`downloader = client.ns.utils.downloader`

**Metode Utama:**
`download(url, audio_only=False)`

| Parameter    | Tipe Data | Default | Deskripsi                                     |
|--------------|-----------|---------|-----------------------------------------------|
| `url`        | `str`     | -       | URL media yang akan diunduh.                    |
| `audio_only` | `bool`    | `False` | Jika `True`, hanya akan mengunduh audio (mp3). |
| **Return**   | `dict`    | -       | `{'path', 'title', 'duration', 'thumbnail'}`  |

**Contoh Penggunaan:**
```python
@app.on_message(filters.command("ytdl"))
async def download_media(client, message):
    if len(message.command) < 2:
        return await message.reply("Sintaks: /ytdl [URL]")
    
    url = message.command[1]
    status = await message.reply("📥 Memproses...")

    try:
        downloader = client.ns.utils.downloader
        result = await downloader.download(url, audio_only=True)
        
        await status.edit("⬆️ Mengunggah audio...")
        await client.send_audio(
            chat_id=message.chat.id, audio=result['path'],
            title=result['title'], duration=result['duration']
        )
        await status.delete()
    except Exception as e:
        await status.edit(f"❌ Gagal: {e}")
```

---

### 8. `encrypt` -> `client.ns.code`
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

---

### 9. `formatter` -> `client.ns.telegram.formatter`
Builder canggih untuk menyusun pesan berformat dengan sintaks yang fasih.

**Inisialisasi:**
`fmt = client.ns.telegram.formatter(mode)`

| Parameter | Tipe Data | Default      | Deskripsi                                 |
|-----------|-----------|--------------|-------------------------------------------|
| `mode`    | `str`     | `"markdown"` | Mode parsing: `"markdown"` atau `"html"`. |

**Contoh Penggunaan:**
```python
fmt = client.ns.telegram.formatter("markdown")
pesan = (
    fmt.bold("🔥 Update Sistem").new_line(2)
    .text("Layanan telah kembali normal.").new_line()
    .italic("Terima kasih atas kesabaran Anda.").new_line()
    .text("Link log: ").link("Klik di sini", "https://example.com/log")
    .to_string()
)
# await message.reply(pesan)
```
---

### 10. `gemini` -> `client.ns.ai.gemini`
Integrasi dengan Google Gemini API untuk fungsionalitas chatbot.

**Inisialisasi:**
`chatbot = client.ns.ai.gemini(api_key)`

**Metode Utama:**
`send_chat_message(message, user_id, bot_name)`

**Contoh Penggunaan:**
```python
chatbot = client.ns.ai.gemini(api_key="API_KEY_GEMINI_ANDA")
jawaban = chatbot.send_chat_message(
    message="jelaskan apa itu relativitas umum dengan bahasa sederhana", 
    user_id="sesi_user_123", # Untuk menjaga histori percakapan
    bot_name="Bot Cerdas"
)
print(jawaban)
```

---

### 11. `gradient` -> `client.ns.utils.grad`
Mempercantik output terminal dengan teks bergradien dan timer countdown.

**Metode Utama:**
- `render_text(text)`
- `countdown(seconds)`

**Contoh Penggunaan:**
```python
# Hanya berjalan di terminal, bukan di bot
client.ns.utils.grad.render_text("Norsodikin")
# await client.ns.utils.grad.countdown(seconds=10)
```
---

### 12. `hf` -> `client.ns.ai.hf` (Direkomendasikan)
Generator gambar AI stabil menggunakan Hugging Face Inference API.

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
    file_gambar = BytesIO(gambar_bytes_list[0])
    # await message.reply_photo(file_gambar, caption=prompt)
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
        umur_msg = await nama_msg.chat.ask(f"OK, {nama_msg.text}. Berapa usiamu?")
        await message.reply(f"Terima kasih! Data tersimpan: Nama={nama_msg.text}, Usia={umur_msg.text}.")
    except asyncio.TimeoutError:
        await message.reply("Waktu habis. Silakan coba lagi.")
```

---

### 14. `local` -> `client.ns.ai.local`
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

### 15. `logger` -> `client.ns.utils.log`
Logger canggih pengganti `print()` yang memberikan output berwarna dan informatif ke konsol.

**Contoh Penggunaan:**
```python
client.ns.utils.log.info("Memulai proses...")
try:
    hasil = 10 / 0
except Exception as e:
    client.ns.utils.log.error(f"Terjadi kesalahan: {e}")
```

---

### 16. `monitor` -> `client.ns.server.monitor`
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

### 17. `payment` -> `client.ns.payment`
Klien terintegrasi untuk berbagai payment gateway populer. (Contoh untuk Midtrans)

**Inisialisasi:**
`midtrans = client.ns.payment.Midtrans(server_key, client_key)`

**Contoh Penggunaan:**
```python
midtrans = client.ns.payment.Midtrans(server_key="SB-SERVER-KEY-ANDA", client_key="SB-CLIENT-KEY-ANDA", is_production=False)
payment_info = midtrans.create_payment(order_id="order-id-123", gross_amount=50000)
print("URL Pembayaran:", payment_info.redirect_url)
```

---

### 18. `process` -> `client.ns.server.process`
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
        
        fmt = client.ns.telegram.formatter("markdown")
        fmt.bold("🔥 Top 5 Proses Berdasarkan Memori").new_line(2)
        
        for p in top_procs:
            fmt.mono(f"PID: {p.pid:<5}").text(f" | RAM: {p.memory_percent:.2f}% | ").bold(p.name).new_line()
        
        await message.reply(fmt.to_string())
    except Exception as e:
        await message.reply(f"Gagal mengambil daftar proses: {e}")
```

---

### 19. `progress` -> `client.ns.utils.progress`
Callback helper untuk menampilkan progress bar dinamis saat mengunggah/mengunduh file dengan Pyrogram.

**Contoh Penggunaan:**
```python
@app.on_message(filters.command("upload"))
async def upload_handler(client, message):
    status = await message.reply("🚀 Mempersiapkan unggahan...")
    progress_bar = client.ns.utils.progress(client, status, task_name="Mengunggah Video")
    await client.send_video(
        chat_id=message.chat.id, 
        video="path/ke/video_besar.mp4", 
        progress=progress_bar.update
    )
    await status.delete()
```

---

### 20. `qrcode` -> `client.ns.ai.qrcode`
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

### 21. `shell` -> `client.ns.utils.shell`
Eksekutor perintah shell/terminal secara asinkron.

**Contoh Penggunaan:**
```python
stdout, stderr, code = await client.ns.utils.shell.run("ls -l /home")
if code == 0:
    await message.reply(f"```\n{stdout}\n```")
else:
    await message.reply(f"Error:\n`{stderr}`")
```
---

### 22. `stt` -> `client.ns.ai.stt`
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

### 23. `storekey` -> `client.ns.data.key`
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

### 24. `translate` -> `client.ns.ai.translate`
Modul AI untuk menerjemahkan teks menggunakan Google Translate API.

**Contoh Penggunaan:**
```python
translator = client.ns.ai.translate()
hasil_id = await translator.to("Hello, world!", dest_lang="id")
print(hasil_id) # Output: Halo Dunia
```

---

### 25. `tts` -> `client.ns.ai.tts`
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

### 28. `web` -> `client.ns.ai.web`
Alat AI untuk melakukan *scraping* konten teks dari URL dan merangkumnya.

**Inisialisasi:** `summarizer = client.ns.ai.web(gemini_instance)`

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("summarize"))
async def summarize_url(client, message):
    url = message.command[1]
    gemini_bot = client.ns.ai.gemini(api_key="GEMINI_API_KEY_ANDA")
    web_summarizer = client.ns.ai.web(gemini_instance=gemini_bot)
    
    status = await message.reply(f"Merangkum konten dari {url}...")
    rangkuman = await web_summarizer.summarize(url)
    await status.edit(f"**Rangkuman Artikel:**\n\n{rangkuman}")
```

---

### 29. `ymlreder` -> `client.ns.data.yaml`
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
---

</details>

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk proyek komersial maupun non-komersial.

---

Semoga dokumentasi yang komprehensif ini membuat pengalaman pengembangan Anda menjadi lebih mudah dan menyenangkan. Selamat mencoba dan berkreasi dengan `norsodikin`! Jika ada pertanyaan atau butuh bantuan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
