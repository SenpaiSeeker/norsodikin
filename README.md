# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan toolkit sakti buat kamu yang mau bikin bot Telegram super canggih, ngelola server, enkripsi data, sampai mainan AI, semuanya jadi lebih gampang dan seru.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas bisa kamu akses langsung lewat `client.ns`, bikin kode bot-mu jadi lebih bersih, rapi, dan intuitif.

## Instalasi

Instalasi `norsodikin` dirancang agar super fleksibel. Anda hanya perlu menginstal apa yang Anda butuhkan.

**1. Instalasi Inti (Sangat Ringan)**
Perintah ini hanya akan menginstal pustaka inti dengan fitur dasar seperti `encrypt`, `payment`, `gemini`, `hf`, dan utilitas umum. Fitur-fitur lain memerlukan dependensi tambahan.

```bash
pip install norsodikin
```

**2. Instalasi dengan Fitur Tambahan (Extras)**
Gunakan "extras" untuk menambahkan dependensi bagi fitur-fitur spesifik. Anda bisa menggabungkan beberapa grup sekaligus. Disarankan menggunakan tanda kutip.

*   **Untuk integrasi Pyrogram:**
    ```bash
    pip install "norsodikin[pyrogram]"
    ```
*   **Untuk semua fitur AI (TTS, Web Summarizer, Bing):**
    ```bash
    pip install "norsodikin[ai]"
    ```
*   **Untuk monitoring server:**
    ```bash
    pip install "norsodikin[server]"
    ```
*   **Untuk menggunakan database MongoDB:**
    ```bash
    pip install "norsodikin[database]"
    ```
*   **Untuk utilitas CLI (seperti gradient banner):**
    ```bash
    pip install "norsodikin[cli]"
    ```
*   **Menggabungkan beberapa fitur (contoh: Pyrogram + AI + Database):**
    ```bash
    pip install "norsodikin[pyrogram,ai,database]"
    ```
*   **Instal Semua Fitur (Sakti Penuh):**
    ```bash
    pip install "norsodikin[all]"
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
## Referensi API Lengkap (`client.ns`)
Berikut adalah panduan mendalam untuk setiap modul yang tersedia.

### 1. `addUser` -> `client.ns.server.user`
Modul ini berfungsi sebagai manajer pengguna SSH jarak jauh di server Linux, memungkinkan Anda menambah dan menghapus pengguna langsung dari skrip Python dan mengirim notifikasi ke Telegram.

**Struktur & Inisialisasi:**
Kelas `SSHUserManager` diinisialisasi dengan kredensial bot Telegram yang akan digunakan untuk mengirim detail login.
```python
user_manager = client.ns.server.user(
    bot_token="TOKEN_BOT_TELEGRAM_ANDA", 
    chat_id=CHAT_ID_TUJUAN_ANDA
)
```

**Contoh Penggunaan Lengkap:**
```python
# Menambah pengguna dengan username dan password acak
user_manager.add_user()

# Menambah pengguna dengan username dan password yang ditentukan
user_manager.add_user(ssh_username="budi", ssh_password="PasswordKuatRahasia123")

# Menghapus pengguna dari sistem
user_manager.delete_user(ssh_username="budi")
```
**Catatan Penting:** Skrip ini memerlukan hak akses `sudo` untuk dapat menjalankan perintah `adduser` dan `deluser` di server.

---

### 2. `argument` -> `client.ns.telegram.arg`
Toolkit untuk mem-parsing dan mengekstrak informasi dari objek `message` Pyrogram. Sangat berguna di dalam message handler untuk mengambil argumen, user, dan alasan.

**Contoh Penggunaan:**
Anggap Anda memiliki handler untuk perintah `/ban @user Pelanggaran berat`.
```python
@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    # Mengambil ID user dan alasan dari pesan
    user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
    if user_id:
        print(f"User yang akan diban: {user_id}")
        print(f"Alasan: {reason or 'Tidak ada alasan'}")

    # Mengambil seluruh teks setelah perintah
    full_args = client.ns.telegram.arg.getMessage(message, is_arg=True)
    print(f"Argumen lengkap: {full_args}")

    # Cek apakah pengirim pesan adalah admin
    is_admin = await client.ns.telegram.arg.getAdmin(message)
    print(f"Apakah pengirim admin? {is_admin}")
    
    # Membuat mention link yang aman untuk log
    me = await client.get_me()
    mention_link = client.ns.telegram.arg.getMention(me, tag_and_id=True)
    print(f"Mention saya dengan ID: {mention_link}")
```

---

### 3. `bing` -> `client.ns.ai.bing` (Tidak Stabil)
Generator gambar AI menggunakan Bing Image Creator. Karena ketergantungan pada *web scraping*, modul ini rentan terhadap perubahan dari sisi Bing. Gunakan dengan hati-hati.

**Struktur & Inisialisasi:**
Membutuhkan cookie autentikasi `_U` dari browser Anda setelah login ke `bing.com/create`.
```python
BING_COOKIE = "NILAI_COOKIE__U_ANDA"
bing_generator = client.ns.ai.bing(auth_cookie_u=BING_COOKIE)
```

**Contoh Penggunaan:**
```python
prompt_gambar = "seekor rubah cyberpunk mengendarai motor di kota neon"
try:
    list_url = await bing_generator.generate(prompt=prompt_gambar, num_images=2)
    print("URL gambar yang dihasilkan:", list_url)
except Exception as e:
    print(f"Gagal membuat gambar: {e}")
```

---

### 4. `button` -> `client.ns.telegram.button`
Perkakas canggih untuk membuat `InlineKeyboardMarkup` dan `ReplyKeyboardMarkup` dengan sintaks yang intuitif, termasuk fitur paginasi otomatis.

**Membuat Inline Keyboard dari Teks**
- **Aturan:** Setiap tombol harus dalam blok `|...|` nya sendiri. Setiap blok membuat baris baru.
- **Gabung Baris:** Gunakan `;same` di akhir data callback untuk menggabungkan tombol ke baris sebelumnya.

```python
teks_inline = """
Pilih opsi:
| 👤 Profil Saya - profil_user |
| 🌐 Website Kami - https://github.com/SenpaiSeeker/norsodikin |
| 📚 Bantuan - bantuan;same |
"""
# Layout: Baris 1: "Profil Saya". Baris 2: "Website Kami" dan "Bantuan".
keyboard_inline, sisa_teks = client.ns.telegram.button.create_inline_keyboard(teks_inline)
# await message.reply(sisa_teks, reply_markup=keyboard_inline)
```

**Membuat Reply Keyboard dari Teks**
- **Aturan:** Semua definisi tombol berada di dalam satu blok `|...|`. Tombol dipisahkan oleh `-`.
- Secara default, setiap tombol membuat baris baru.
- **Gabung Baris:** Gunakan `;same` untuk meletakkan tombol di baris yang sama dengan tombol sebelumnya.
- **Tombol Khusus:** Gunakan `;is_contact` untuk meminta kontak.

```python
teks_reply = """
Selamat datang!
| 📞 Bagikan Kontak;is_contact - 📚 Bantuan - ⚙️ Pengaturan;same |
"""
# Layout: Baris 1: "Bagikan Kontak". Baris 2: "Bantuan" dan "Pengaturan".
keyboard_reply, sisa_teks_reply = client.ns.telegram.button.create_button_keyboard(teks_reply)
# await message.reply(sisa_teks_reply, reply_markup=keyboard_reply)
```

**Membuat Paginasi (Halaman Tombol) Otomatis**
```python
list_produk = [{"text": f"Produk #{i}", "data": i} for i in range(1, 31)]
keyboard_paginasi = client.ns.telegram.button.create_pagination_keyboard(
    items=list_produk, current_page=2, items_per_page=6, items_per_row=2,
    callback_prefix="nav_produk", item_callback_prefix="pilih_produk",
    extra_params=[{"text": "« Kembali", "callback_data": "menu_utama"}]
)
# await message.reply("Daftar produk:", reply_markup=keyboard_paginasi)
```
---

### 5. `database` -> `client.ns.data.db`
Sistem database fleksibel yang mendukung penyimpanan lokal (JSON), SQLite, dan MongoDB, dengan enkripsi data otomatis.

**Bagian 1: Inisialisasi Database**
Pilih backend penyimpanan Anda saat inisialisasi.

```python
# Opsi 1: JSON Lokal (Default, paling sederhana)
db = client.ns.data.db()

# Opsi 2: SQLite (Lebih Cepat dan Robust)
db_sqlite = client.ns.data.db(storage_type="sqlite", file_name="bot_data")

# Opsi 3: MongoDB (Skalabilitas Tinggi)
db_mongo = client.ns.data.db(
    storage_type="mongo",
    mongo_url="mongodb://user:pass@host:port/"
)

# Opsi 4: Inisialisasi Lanjutan dengan Semua Parameter
db_full = client.ns.data.db(
    storage_type="sqlite",
    file_name="production_db",
    keys_encrypt="KUNCI_ENKRIPSI_SANGAT_RAHASIA_ANDA",
    method_encrypt="bytes",
    auto_backup=True,
    backup_bot_token="TOKEN_BOT_UNTUK_BACKUP",
    backup_chat_id="ID_CHAT_TUJUAN_BACKUP",
    backup_interval_hours=24
)
```

**Bagian 2: Operasi Data Dasar (Variabel Tunggal)**
Gunakan `setVars`, `getVars`, dan `removeVars`. Parameter `var_key` berfungsi seperti "folder" untuk mengorganisir data.

```python
user_id = 12345
db.setVars(user_id, "nama", "Budi", var_key="profil")
nama = db.getVars(user_id, "nama", var_key="profil")
db.removeVars(user_id, "kota", var_key="profil")
```

**Bagian 3: Bekerja dengan List**
Gunakan `setListVars`, `getListVars`, dan `removeListVars`.

```python
user_id = 12345
db.setListVars(user_id, "item", "Apel", var_key="keranjang")
items = db.getListVars(user_id, "item", var_key="keranjang")
db.removeListVars(user_id, "item", "Apel", var_key="keranjang")
```

**Bagian 4: Manajemen Masa Aktif Pengguna**
Kelola akses pengguna berbasis waktu.

```python
user_id = 12345
db.setExp(user_id, exp=30)
sisa_hari = db.daysLeft(user_id)
if db.checkAndDeleteIfExpired(user_id): print("Pengguna kedaluwarsa.")
```

**Bagian 5: Penyimpanan Khusus Bot (Userbot/Bot)**
Simpan sesi Pyrogram atau token bot dengan aman.

```python
user_id = 12345
db.saveBot(user_id, api_id=123, api_hash="abc", value="SESSION_STRING_ANDA")
db.saveBot(user_id, api_id=456, api_hash="def", value="TOKEN_BOT_ANDA", is_token=True)
semua_userbot = db.getBots()
semua_bot = db.getBots(is_token=True)
```

---

### 6. `encrypt` -> `client.ns.code`
Koleksi kelas untuk enkripsi dan dekripsi data.

**Struktur & Inisialisasi:**
```python
cipher = client.ns.code.Cipher(key="kunci-rahasia", method="bytes")
ascii_manager = client.ns.code.Ascii(key="kunci-lain")
```

**Contoh Penggunaan:**
```python
data_asli = {"id": 123, "plan": "premium"}
terenkripsi_hex = cipher.encrypt(data_asli)
didekripsi_kembali = cipher.decrypt(terenkripsi_hex)
```

---

### 7. `formatter` -> `client.ns.telegram.formatter`
Builder canggih untuk menyusun pesan berformat dengan sintaks Markdown kustom atau mode HTML standar.

**Struktur & Inisialisasi:**
```python
fmt_md = client.ns.telegram.formatter("markdown")
fmt_html = client.ns.telegram.formatter("html")
```
Sintaks Markdown Kustom: `**Bold**`, `__Italic__`, `--Underline--`, `~~Strike~~`, `||Spoiler||`, `\`Code\``.

**Contoh Penggunaan:**
```python
pesan_md = (
    fmt_md.bold("Update Sistem").new_line()
    .underline("Layanan Pulih").new_line()
    .italic("Terima kasih atas kesabaran Anda.").new_line()
    .pre("22:00 - Outage\n22:30 - Stable")
    .to_string()
)
# await message.reply(pesan_md)
```

---

### 8. `gemini` -> `client.ns.ai.gemini`
Integrasi dengan Google Gemini API untuk fungsionalitas chatbot.

**Struktur & Inisialisasi:**
```python
GEMINI_KEY = "API_KEY_GEMINI_ANDA"
chatbot = client.ns.ai.gemini(api_key=GEMINI_KEY)
```

**Contoh Penggunaan:**
```python
user_id = "sesi_unik_123"
jawaban = chatbot.send_chat_message("jelaskan relativitas", user_id, "Bot Cerdas")
```

---

### 9. `gradient` -> `client.ns.utils.grad`
Mempercantik output terminal dengan teks bergradien dan timer countdown.

**Contoh Penggunaan:**
```python
import asyncio
client.ns.utils.grad.render_text("Norsodikin")
await client.ns.utils.grad.countdown(10, text="Sisa waktu: {time}")
```

---

### 10. `hf` -> `client.ns.ai.hf` (Direkomendasikan)
Generator gambar AI stabil menggunakan Hugging Face Inference API.

**Struktur & Inisialisasi:**
```python
HF_TOKEN = "hf_TOKEN_ANDA"
hf_generator = client.ns.ai.hf(api_key=HF_TOKEN)
```

**Contoh Penggunaan:**
```python
from io import BytesIO
list_bytes = await hf_generator.generate("foto penyihir di perpustakaan", num_images=1)
gambar = BytesIO(list_bytes[0])
gambar.name = "hasil.png"
# await message.reply_photo(gambar)
```

---

### 11. `listen` -> `client.listen()` & `chat.ask()`
*Monkey-patching* untuk Pyrogram yang menambahkan alur percakapan interaktif.

**Aktivasi:** Cukup `from nsdev import listen` di awal skrip.

**Contoh Penggunaan:**
```python
@app.on_message(filters.command("register"))
async def register(client, message):
    try:
        nama = await message.chat.ask("Siapa namamu?", timeout=60)
        umur = await message.chat.ask(f"Halo {nama.text}! Berapa usiamu?")
        await message.reply(f"Data tersimpan: {nama.text}, {umur.text} tahun")
    except asyncio.TimeoutError:
        await message.reply("Waktu habis.")
```

---

### 12. `logger` -> `client.ns.utils.log`
Logger canggih pengganti `print()` yang memberikan output berwarna dan informatif ke konsol.

**Struktur & Inisialisasi:**
Logger dapat dikustomisasi saat diinisialisasi untuk mengubah format output atau zona waktu.
```python
# Inisialisasi default (WIB, format standar)
log = client.ns.utils.log

# Inisialisasi kustom
custom_log = client.ns.utils.log.__class__(
    tz='America/New_York', # Zona waktu
    fmt='{asctime} [{levelname}] {message}', # Format log yang lebih simpel
    datefmt='%H:%M:%S' # Format waktu
)
```

**Contoh Penggunaan:**
```python
client.ns.utils.log.info("Memulai proses penting...")
data = {"id": 42, "user": "admin"}
client.ns.utils.log.debug(f"Data yang diterima: {data}")
try:
    100 / 0
except Exception as e:
    client.ns.utils.log.error(f"Terjadi kesalahan fatal: {e}")
```

---

### 13. `monitor` -> `client.ns.server.monitor`
Utilitas sederhana untuk memantau penggunaan sumber daya server Linux (CPU, RAM, Disk) secara real-time.

**Struktur & Return Value:**
Metode `get_stats()` mengembalikan objek `SimpleNamespace` yang berisi:
- `cpu_percent`, `ram_total_gb`, `ram_used_gb`, `ram_percent`, `disk_total_gb`, `disk_used_gb`, `disk_percent`.

**Contoh Penggunaan:**
```python
stats = client.ns.server.monitor.get_stats()
fmt = client.ns.telegram.formatter("markdown")
pesan_status = (
    fmt.bold("🖥️ Status Server").new_line(2)
    .text("▫️ CPU Load: ").mono(f"{stats.cpu_percent}%").new_line()
    .text("▫️ RAM Usage: ").mono(f"{stats.ram_used_gb:.2f} / {stats.ram_total_gb:.2f} GB ({stats.ram_percent}%)").new_line()
    .to_string()
)
# await message.reply(pesan_status)
```

---

### 14. `payment` -> `client.ns.payment`
Klien terintegrasi untuk berbagai payment gateway populer di Indonesia.

**A. Midtrans**
```python
midtrans = client.ns.payment.Midtrans(
    server_key="SERVER_KEY_ANDA", client_key="CLIENT_KEY_ANDA", is_production=False
)
payment_info = midtrans.create_payment(order_id="order-123", gross_amount=50000)
status = midtrans.check_transaction(order_id="order-123")
```

**B. Tripay**
```python
tripay = client.ns.payment.Tripay(api_key="API_KEY_TRIPAY_ANDA")
payment_data = tripay.create_payment(
    method="QRIS", amount=25000, order_id="order-456", customer_name="Budi"
)
status = tripay.check_transaction(reference=payment_data.data.reference)
```

**C. VioletMediaPay**
```python
violet = client.ns.payment.Violet(
    api_key="API_KEY_VIOLET_ANDA", secret_key="SECRET_KEY_VIOLET_ANDA", live=True 
)
payment_result = await violet.create_payment(channel_payment="QRIS", amount="10000")
if payment_result.status:
    status = await violet.check_transaction(ref=payment_result.data.ref_kode, ref_id=payment_result.data.id_reference)
```

---

### 15. `progress` -> `client.ns.utils.progress`
Callback helper untuk menampilkan progress bar dinamis saat mengunggah atau mengunduh file besar dengan Pyrogram.

**Alur Kerja:**
1.  Kirim pesan awal (placeholder).
2.  Inisialisasi `TelegramProgressBar` dengan `client` dan `message` dari langkah 1.
3.  Gunakan metode `.update` dari objek progress bar sebagai nilai parameter `progress`.

**Contoh Penggunaan:**
```python
pesan_status = await message.reply("🚀 Mempersiapkan unggahan...")
progress_bar = client.ns.utils.progress(
    client=client, message=pesan_status, task_name="Uploading Video.mp4"
)
await client.send_video(
    chat_id=message.chat.id, video="path/ke/video.mp4", progress=progress_bar.update
)
await pesan_status.edit("✅ Unggah Selesai!")
```

---

### 16. `storekey` -> `client.ns.data.key`
Manajer untuk menangani kunci rahasia dan nama file environment dari argumen terminal, mencegah *hardcoding* kredensial.

**1. Cara Menjalankan di Terminal:**
```bash
python3 main.py --key kunci-rahasia-anda --env config.env
```

**2. Cara Menggunakan di Kode Python:**
```python
key_manager = client.ns.data.key()
try:
    kunci_rahasia, nama_file_env = key_manager.handle_arguments()
    print(f"Menggunakan Kunci: {kunci_rahasia}")
except SystemExit:
    print("Skrip dihentikan karena argumen tidak lengkap.")
```
---

### 17. `tts` -> `client.ns.ai.tts`
Modul AI untuk mengubah teks menjadi pesan suara (Text-to-Speech) menggunakan API Google.

**Struktur & Inisialisasi:**
Kelas ini tidak memerlukan parameter saat inisialisasi. Metode `generate` menerima `text` dan `lang` (kode bahasa, default 'id').

**Contoh Penggunaan:**
```python
from io import BytesIO
tts_generator = client.ns.ai.tts()
audio_bytes = await tts_generator.generate(text="Halo, ini pesan suara otomatis.", lang="id")
file_suara = BytesIO(audio_bytes)
file_suara.name = "notifikasi.ogg"
# await message.reply_voice(file_suara, caption="Pesan Suara Penting!")
```

---

### 18. `web` -> `client.ns.ai.web`
Alat AI canggih untuk melakukan *scraping* konten teks dari sebuah URL dan merangkumnya menggunakan model Gemini.

**Struktur & Inisialisasi:**
**Penting:** Kelas ini *harus* diinisialisasi dengan sebuah instance dari `gemini` yang sudah dibuat sebelumnya.
```python
# 1. Buat instance Gemini terlebih dahulu
gemini_bot = client.ns.ai.gemini(api_key="GEMINI_API_KEY_ANDA")

# 2. Berikan instance tersebut saat membuat WebSummarizer
web_summarizer = client.ns.ai.web(gemini_instance=gemini_bot)
```
Metode `summarize` menerima `url` dan `max_length` (opsional, default 8000 karakter) untuk membatasi teks yang dikirim ke AI.

**Contoh Penggunaan:**
```python
url_berita = "https://www.cnbcindonesia.com/news/20231120094757-4-490311/jokowi-buka-bukaan-minta-biden-dorong-gencatan-senjata-gaza"
await message.reply("⏳ Sedang membaca dan merangkum artikel...")

# Memulai proses peringkasan dengan panjang teks maksimal 2048 karakter
rangkuman = await web_summarizer.summarize(url_berita, max_length=2048)

# Tampilkan hasilnya
# await message.reply(f"📄 **Rangkuman:**\n\n{rangkuman}")
```

---

### 19. `ymlreder` -> `client.ns.data.yaml`
Utilitas praktis untuk membaca file konfigurasi `.yml` dan mengubahnya menjadi objek Python yang bisa diakses dengan notasi titik (`.`).

**Cara Kerja:**
Fungsi `loadAndConvert` membaca file YAML dan mengubah struktur bersarangnya menjadi objek `SimpleNamespace`. Ini memungkinkan Anda mengakses nilai-nilai seperti `config.database.host` alih-alih `config['database']['host']`.

**Contoh File `config.yml`:**
```yaml
app:
  name: "Bot Canggih"
  version: "1.2.0"
api_keys:
  - name: "google"
    key: "key-123"
  - name: "openai"
    key: "key-456"
database:
  host: "localhost"
  port: 5432
  user: "admin"
```

**Contoh Kode:**
```python
# Muat dan konversi file YAML
config = client.ns.data.yaml.loadAndConvert("config.yml")

if config:
    # Akses konfigurasi dengan mudah menggunakan notasi titik
    print(f"Nama Aplikasi: {config.app.name} (v{config.app.version})")
    print(f"Host Database: {config.database.host}:{config.database.port}")
    
    # Bekerja dengan list
    for api in config.api_keys:
        print(f"API {api.name}: {api.key}")
else:
    print("Gagal memuat file konfigurasi.")
```

---
## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, kamu bebas pakai, modifikasi, dan distribusikan untuk proyek apa pun.

---

Semoga dokumentasi ini bikin kamu makin semangat ngoding! Selamat mencoba dan berkreasi dengan `norsodikin`. Jika ada pertanyaan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
