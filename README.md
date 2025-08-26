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
*   **Untuk semua fitur AI (TTS, Web Summarizer, Bing, Translate, QR Code):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[ai]"
    ```
    > **Catatan Penting untuk Pembaca QR Code:**
    > Fitur `qrcode.read()` memerlukan library `zbar`. Jika Anda menggunakan sistem berbasis Debian/Ubuntu, instal dengan perintah:
    > `sudo apt-get update && sudo apt-get install -y libzbar0`

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
*   **Menggabungkan beberapa fitur (contoh: Pyrogram + AI + Database):**
    ```bash
    pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[pyrogram,ai,database]"
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
<summary><h2><strong>Referensi API Lengkap (Klik untuk Buka/Tutup)</strong></h2></summary>

Berikut adalah panduan mendalam untuk setiap modul yang tersedia.

### 1. `actions` -> `client.ns.telegram.actions`
Modul untuk menampilkan status *chat action* (seperti "typing...", "uploading photo...") secara otomatis selama sebuah proses berjalan. Ini memberikan feedback visual kepada pengguna bahwa bot sedang sibuk.

**Struktur & Inisialisasi:**
Modul ini digunakan sebagai *context manager* (`async with`), yang akan memulai dan menghentikan pengiriman *chat action* secara otomatis.

**Contoh Penggunaan Lengkap:**
```python
import asyncio

# @app.on_message(...)
async def long_process_handler(client, message):
    # Bot akan menampilkan status "typing..." selama 5 detik
    await message.reply("Saya akan berpura-pura sibuk mengetik selama 5 detik...")
    async with client.ns.telegram.actions.typing(message.chat.id):
        await asyncio.sleep(5)
    
    # Bot akan menampilkan "uploading video..." selama proses upload
    await message.reply("Sekarang saya akan upload video (simulasi)...")
    async with client.ns.telegram.actions.upload_video(message.chat.id):
        # ... kode untuk proses upload file video Anda di sini ...
        await asyncio.sleep(8)
    
    await message.reply("Selesai!")

```
**Metode yang Tersedia:**
- `.typing(chat_id)`
- `.upload_photo(chat_id)`
- `.upload_video(chat_id)`
- `.record_video(chat_id)`
- `.record_voice(chat_id)`

---

### 2. `addUser` -> `client.ns.server.user`
Modul ini berfungsi sebagai manajer pengguna SSH jarak jauh di server Linux, memungkinkan Anda menambah dan menghapus pengguna langsung dari skrip Python dan mengirim notifikasi ke Telegram.

**Struktur & Inisialisasi:**
Kelas `SSHUserManager` diinisialisasi dengan kredensial bot Telegram yang akan digunakan untuk mengirim detail login.

- **Parameter Wajib:**
  - `bot_token` (`str`): Token bot Telegram Anda.
  - `chat_id` (`int`|`str`): ID chat tujuan untuk notifikasi.

```python
user_manager = client.ns.server.user(
    bot_token="TOKEN_BOT_TELEGRAM_ANDA", 
    chat_id=CHAT_ID_TUJUAN_ANDA
)
```

**Contoh Penggunaan Lengkap:**
```python
# Menambah pengguna dengan username dan password acak
# Detail login akan dikirim ke chat_id yang dikonfigurasi
user_manager.add_user()

# Menambah pengguna dengan username dan password yang ditentukan
user_manager.add_user(
    ssh_username="budi", 
    ssh_password="PasswordKuatRahasia123"
)

# Menghapus pengguna dari sistem
user_manager.delete_user(ssh_username="budi")
```
**Catatan Penting:** Skrip ini memerlukan hak akses `sudo` untuk dapat menjalankan perintah `adduser` dan `deluser` di server.

---

### 3. `argument` -> `client.ns.telegram.arg`
Toolkit untuk mem-parsing dan mengekstrak informasi dari objek `message` Pyrogram. Sangat berguna di dalam message handler untuk mengambil argumen, user, dan alasan.

**Contoh Penggunaan:**
Anggap Anda memiliki handler untuk perintah `/ban @user Pelanggaran berat`.
```python
@app.on_message(filters.command("ban"))
async def ban_user(client, message):
    # Mengambil ID user dan alasan dari pesan
    # Bekerja untuk reply, username (@user), dan user ID
    user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
    if user_id:
        print(f"User yang akan diban: {user_id}")
        print(f"Alasan: {reason or 'Tidak ada alasan'}")
    else:
        print("User tidak ditemukan.")

    # Mengambil seluruh teks setelah perintah
    full_args = client.ns.telegram.arg.getMessage(message, is_arg=True)
    print(f"Argumen lengkap: {full_args}")

    # Cek apakah pengirim pesan adalah admin di grup
    is_admin = await client.ns.telegram.arg.getAdmin(message)
    print(f"Apakah pengirim admin? {is_admin}")
    
    # Membuat mention link yang aman untuk log
    me = await client.get_me()
    mention_link = client.ns.telegram.arg.getMention(me, tag_and_id=True)
    print(f"Mention saya dengan ID: {mention_link}")
```

---

### 4. `bing` -> `client.ns.ai.bing` (Tidak Stabil)
Generator gambar AI menggunakan Bing Image Creator. Karena ketergantungan pada *web scraping*, modul ini rentan terhadap perubahan dari sisi Bing. Gunakan dengan hati-hati.

**Struktur & Inisialisasi:**
Membutuhkan cookie autentikasi `_U` dari browser Anda setelah login ke `bing.com/create`.

- **Parameter Wajib:**
  - `auth_cookie_u` (`str`): Nilai cookie `_U` dari bing.com.

```python
BING_COOKIE = "NILAI_COOKIE__U_ANDA"
bing_generator = client.ns.ai.bing(auth_cookie_u=BING_COOKIE)
```

**Contoh Penggunaan:**
```python
prompt_gambar = "seekor rubah cyberpunk mengendarai motor di kota neon"
try:
    # Parameter opsional: num_images (default: 4), max_wait_seconds (default: 300)
    list_url = await bing_generator.generate(
        prompt=prompt_gambar, 
        num_images=2
    )
    print("URL gambar yang dihasilkan:", list_url)
    # Anda bisa mengirim URL ini langsung ke Telegram
    # for url in list_url:
    #     await message.reply_photo(url)
except Exception as e:
    print(f"Gagal membuat gambar: {e}")
```

---

### 5. `button` -> `client.ns.telegram.button`
Perkakas canggih untuk membuat `InlineKeyboardMarkup` dan `ReplyKeyboardMarkup` dengan sintaks yang intuitif, termasuk fitur paginasi otomatis.

**Membuat Inline Keyboard dari Teks**
- **Aturan:** Setiap tombol harus dalam blok `|...|`. Setiap blok membuat baris baru.
- **Format:** `| Teks Tombol - data_callback_atau_url |`
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

**Membuat Paginasi (Halaman Tombol) Otomatis**
Fungsi `create_pagination_keyboard` secara otomatis membuat keyboard berhalaman untuk daftar yang panjang.
```python
list_produk = [{"text": f"Produk #{i}", "data": f"prod_{i}"} for i in range(1, 31)]
halaman_sekarang = 2 # Halaman yang ingin ditampilkan

# Membuat keyboard paginasi
keyboard_paginasi = client.ns.telegram.button.create_pagination_keyboard(
    items=list_produk,                      # list item, bisa dict atau string
    current_page=halaman_sekarang,          # halaman saat ini
    items_per_page=6,                       # jumlah item per halaman (opsional, default 5)
    items_per_row=2,                        # jumlah item per baris (opsional, default 1)
    callback_prefix="nav_produk",           # prefix untuk callback navigasi (e.g., "nav_produk_1")
    item_callback_prefix="pilih_produk",    # prefix untuk callback item (e.g., "pilih_produk_prod_5")
    extra_params=[                          # tombol tambahan di bagian bawah
        {"text": "« Kembali ke Menu", "callback_data": "menu_utama"},
    ]
)
# await message.reply("Daftar produk (Halaman 2 dari 5):", reply_markup=keyboard_paginasi)
```
---

### 6. `database` -> `client.ns.data.db`
Sistem database fleksibel yang mendukung penyimpanan lokal (JSON), SQLite, dan MongoDB, dengan enkripsi data otomatis.

**Inisialisasi Database**
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
    keys_encrypt="KUNCI_ENKRIPSI_SANGAT_RAHASIA_ANDA", # Ganti dengan kunci Anda sendiri!
    method_encrypt="bytes", # Pilihan: 'bytes', 'shift', 'binary'
    auto_backup=True,
    backup_bot_token="TOKEN_BOT_UNTUK_BACKUP",
    backup_chat_id="ID_CHAT_TUJUAN_BACKUP",
    backup_interval_hours=24 # Backup setiap 24 jam
)
```

**Operasi Data Dasar (CRUD)**
Gunakan `setVars`, `getVars`, `setListVars`, `getListVars`, `removeVars` dll. Parameter `var_key` berfungsi seperti "folder" untuk mengorganisir data.

```python
user_id = 12345
# Menyimpan string
db.setVars(user_id, "nama", "Budi", var_key="profil")
# Menyimpan list
db.setListVars(user_id, "hobi", "Membaca", var_key="profil")
db.setListVars(user_id, "hobi", "Ngoding", var_key="profil")
# Mendapatkan data
nama = db.getVars(user_id, "nama", var_key="profil")
hobi_list = db.getListVars(user_id, "hobi", var_key="profil")
print(f"{nama} punya hobi: {hobi_list}") # Output: Budi punya hobi: ['Membaca', 'Ngoding']

# Mengelola masa aktif user
db.setExp(user_id, exp=30) # User aktif selama 30 hari
sisa_hari = db.daysLeft(user_id)
print(f"Sisa masa aktif: {sisa_hari} hari")

if db.checkAndDeleteIfExpired(user_id):
    print("Pengguna kedaluwarsa dan datanya telah dihapus.")
```
---

### 7. `encrypt` -> `client.ns.code`
Koleksi kelas untuk enkripsi dan dekripsi data dengan berbagai metode.

**Struktur & Inisialisasi:**
- **Parameter `CipherHandler`:**
  - `key` (`str`): Kunci rahasia untuk enkripsi.
  - `method` (`str`): Metode enkripsi. Pilihan: `bytes` (direkomendasikan), `shift`, `binary`.
- **Parameter `AsciiManager`:**
  - `key` (`str`): Kunci rahasia untuk enkripsi berbasis ASCII offset.

```python
# Direkomendasikan
cipher_bytes = client.ns.code.Cipher(key="kunci-rahasia-super-aman-123", method="bytes")

# Metode alternatif
cipher_shift = client.ns.code.Cipher(key="kunci-shift", method="shift")
ascii_manager = client.ns.code.Ascii(key="kunci-lain-lagi")
```

**Contoh Penggunaan:**
```python
data_asli = {"id": 123, "plan": "premium", "user": "Budi"}

# Enkripsi
terenkripsi_hex = cipher_bytes.encrypt(data_asli)
print(f"Data Terenkripsi (hex): {terenkripsi_hex}")

# Dekripsi
didekripsi_kembali = cipher_bytes.decrypt(terenkripsi_hex)
print(f"Data Didekripsi: {didekripsi_kembali}")
print(f"Tipe data setelah dekripsi: {type(didekripsi_kembali)}")
```

---

### 8. `formatter` -> `client.ns.telegram.formatter`
Builder canggih untuk menyusun pesan berformat dengan sintaks Markdown kustom atau mode HTML standar.

**Struktur & Inisialisasi:**
- **Parameter:** `mode` (`str`) - "markdown" (default) atau "html".

```python
fmt = client.ns.telegram.formatter("markdown") # Atau "html"
```
Sintaks Markdown Kustom: `**Bold**`, `__Italic__`, `--Underline--`, `~~Strike~~`, `||Spoiler||`, `\`Code\``.

**Contoh Penggunaan:**
```python
pesan_terformat = (
    fmt.bold("🔥 Update Sistem Penting 🔥").new_line(2)
    .text("Halo semua, kami ingin menginformasikan bahwa:").new_line()
    .underline("Semua Layanan Telah Kembali Normal").new_line()
    .italic("Terima kasih atas kesabaran Anda selama perbaikan.").new_line(2)
    .mono("Kode insiden: SRV-2024-08-XYZ").new_line()
    .link("Lihat log lengkap di sini", "https://github.com/SenpaiSeeker/norsodikin")
    .to_string()
)
# await message.reply(pesan_terformat, disable_web_page_preview=True)
```
---

### 9. `gemini` -> `client.ns.ai.gemini`
Integrasi dengan Google Gemini API untuk fungsionalitas chatbot dan fitur AI kreatif lainnya seperti "Cek Khodam".

**Struktur & Inisialisasi:**
- **Parameter Wajib:**
  - `api_key` (`str`): Kunci API Google Gemini Anda.

```python
GEMINI_KEY = "API_KEY_GEMINI_ANDA"
chatbot = client.ns.ai.gemini(api_key=GEMINI_KEY)
```

**Contoh 1: Chatbot Umum**
```python
user_id = "sesi_unik_pengguna_123"
bot_name = "Bot Cerdas" # Nama bot Anda untuk salam pembuka
pertanyaan = "jelaskan apa itu lubang hitam secara sederhana"
jawaban = chatbot.send_chat_message(pertanyaan, user_id, bot_name)

print(jawaban)
# await message.reply(jawaban)
```

**Contoh 2: Fitur "Cek Khodam" (Hiburan)**
Fungsi `send_khodam_message` menggunakan instruksi sistem khusus untuk menghasilkan deskripsi "khodam" berdasarkan nama.
```python
user_id = message.from_user.id # Gunakan ID user untuk memisahkan sesi
nama_pengguna = message.from_user.first_name
deskripsi_khodam = chatbot.send_khodam_message(nama_pengguna, user_id)

pesan_khodam = (
    fmt.bold(f"✨ Khodam Terdeteksi untuk {nama_pengguna} ✨").new_line(2)
    .text(deskripsi_khodam)
    .to_string()
)
# await message.reply(pesan_khodam)
```

---

### 10. `gradient` -> `client.ns.utils.grad`
Mempercantik output terminal dengan teks bergradien dan timer countdown. Berguna untuk CLI atau saat menjalankan bot dari konsol.

**Contoh Penggunaan:**
```python
import asyncio

# Menampilkan banner teks dengan warna gradien
client.ns.utils.grad.render_text("Norsodikin")

# Menjalankan timer countdown di terminal
await client.ns.utils.grad.countdown(
    seconds=10, 
    text="Bot akan dimulai dalam: {time}"
)
print("\nBot dimulai!")
```

---

### 11. `hf` -> `client.ns.ai.hf` (Direkomendasikan)
Generator gambar AI stabil menggunakan Hugging Face Inference API. Alternatif yang lebih andal dibandingkan `bing`.

**Struktur & Inisialisasi:**
- **Parameter Wajib:**
  - `api_key` (`str`): Token API Hugging Face Anda (biasanya dimulai dengan `hf_`).
- **Parameter Opsional:**
  - `model_id` (`str`): ID model di Hugging Face Hub (default: `stabilityai/stable-diffusion-xl-base-1.0`).

```python
HF_TOKEN = "hf_TOKEN_ANDA"
hf_generator = client.ns.ai.hf(
    api_key=HF_TOKEN, 
    model_id="runwayml/stable-diffusion-v1-5" # Contoh menggunakan model lain
)
```

**Contoh Penggunaan:**
```python
from io import BytesIO

prompt = "foto seorang astronot duduk santai di pantai mars, gaya realistis"
try:
    # Generate 1 gambar
    list_bytes = await hf_generator.generate(prompt, num_images=1)
    
    if list_bytes:
        gambar_bytes = list_bytes[0]
        # Kirim sebagai file
        file_gambar = BytesIO(gambar_bytes)
        file_gambar.name = "hasil-ai.png"
        # await message.reply_photo(file_gambar, caption=f"Prompt: {prompt}")
except Exception as e:
    print(f"Gagal membuat gambar: {e}")
```

---

### 12. `listen` -> `client.listen()` & `chat.ask()`
*Monkey-patching* untuk Pyrogram yang menambahkan alur percakapan interaktif, memungkinkan bot untuk "menunggu" jawaban dari pengguna.

**Aktivasi:** Cukup `from nsdev import listen` di awal skrip utama Anda.

**Contoh Penggunaan:**
```python
import asyncio
from nsdev import listen # Wajib di-import

# @app.on_message(filters.command("register"))
async def register(client, message):
    try:
        nama_msg = await message.chat.ask(
            "Halo! Siapa namamu?", 
            timeout=30 # Waktu tunggu dalam detik (opsional)
        )
        
        umur_msg = await message.chat.ask(
            f"Senang bertemu, {nama_msg.text}! Sekarang, berapa usiamu?",
            filters=filters.regex(r"^\d+$"), # Hanya menerima angka (opsional)
            timeout=30
        )
        
        await message.reply(
            f"Terima kasih! Data kamu tersimpan:\n"
            f"Nama: {nama_msg.text}\n"
            f"Umur: {umur_msg.text} tahun"
        )
    except asyncio.TimeoutError:
        await message.reply("Waktu habis. Silakan coba lagi /register.")
    except Exception as e:
        await message.reply(f"Terjadi error: {e}")
```

---

### 13. `logger` -> `client.ns.utils.log`
Logger canggih pengganti `print()` yang memberikan output berwarna, berformat, dan informatif ke konsol.

**Penggunaan Dasar (Tanpa Konfigurasi):**
```python
client.ns.utils.log.info("Memulai proses penting...")
data = {"id": 42, "user": "admin"}
client.ns.utils.log.debug(f"Data yang diterima: {data}")

try:
    hasil = 100 / 0
except Exception as e:
    # Error akan ditampilkan dengan warna merah dan detail lengkap
    client.ns.utils.log.error(f"Terjadi kesalahan fatal saat pembagian: {e}")
client.ns.utils.log.warning("Ini adalah peringatan, proses tetap berjalan.")
```

**Inisialisasi Kustom (Opsional):**
Anda bisa membuat instance logger baru dengan konfigurasi berbeda.
```python
# Membuat logger baru untuk modul spesifik
payment_logger = client.ns.utils.log.__class__(
    tz='America/New_York', # Zona waktu
    fmt='{asctime} [{levelname}] [PAYMENT] {message}', # Format log yang lebih simpel
    datefmt='%H:%M:%S' # Format waktu
)
payment_logger.info("Memproses pembayaran...")
```

---

### 14. `monitor` -> `client.ns.server.monitor`
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
    .text("▫️ Disk Usage: ").mono(f"{stats.disk_used_gb:.2f} / {stats.disk_total_gb:.2f} GB ({stats.disk_percent}%)").new_line()
    .to_string()
)
# await message.reply(pesan_status)
```

---

### 15. `payment` -> `client.ns.payment`
Klien terintegrasi untuk berbagai payment gateway populer di Indonesia.

**A. Midtrans**
```python
midtrans = client.ns.payment.Midtrans(
    server_key="SERVER_KEY_ANDA", 
    client_key="CLIENT_KEY_ANDA", 
    is_production=False # Set True untuk mode produksi
)
payment_info = midtrans.create_payment(
    order_id="order-xyz-12345", 
    gross_amount=50000
)
print("URL Pembayaran Midtrans:", payment_info.redirect_url)

# Untuk mengecek status
status = midtrans.check_transaction(order_id="order-xyz-12345")
print("Status Transaksi:", status.transaction_status)
```

**B. Tripay**
```python
tripay = client.ns.payment.Tripay(api_key="API_KEY_TRIPAY_ANDA")
payment_data = tripay.create_payment(
    method="QRIS", 
    amount=25000, 
    order_id="order-abc-67890", 
    customer_name="Budi"
)
print("Referensi Tripay:", payment_data.data.reference)
print("URL Checkout:", payment_data.data.checkout_url)
```

---

### 16. `progress` -> `client.ns.utils.progress`
Callback helper untuk menampilkan progress bar dinamis saat mengunggah atau mengunduh file besar dengan Pyrogram.

**Alur Kerja:**
1.  Kirim pesan awal (placeholder).
2.  Inisialisasi `TelegramProgressBar` dengan `client` dan `message` dari langkah 1.
3.  Gunakan metode `.update` dari objek progress bar sebagai nilai parameter `progress` di fungsi Pyrogram.

**Contoh Penggunaan:**
```python
# @app.on_message(filters.command("upload"))
async def upload_handler(client, message):
    pesan_status = await message.reply("🚀 Mempersiapkan unggahan...")
    progress_bar = client.ns.utils.progress(
        client=client, 
        message=pesan_status, 
        task_name="Uploading Video.mp4"
    )

    try:
        await client.send_video(
            chat_id=message.chat.id, 
            video="path/ke/video_besar.mp4", 
            caption="Ini video besar yang diunggah dengan progress bar.",
            progress=progress_bar.update # Ini kuncinya!
        )
        await pesan_status.delete() # Hapus pesan progress setelah selesai
    except Exception as e:
        await pesan_status.edit(f"Gagal mengunggah: {e}")

```
---

### 17. `qrcode` -> `client.ns.ai.qrcode`
Modul AI untuk membuat dan membaca gambar QR Code.

**Inisialisasi:**
```python
qr_manager = client.ns.ai.qrcode()
```

#### **A. Membuat QR Code**
Metode `generate(data: str)` mengubah teks atau URL menjadi gambar QR Code.

**Contoh Penggunaan:**
```python
from io import BytesIO

teks_atau_url = "https://github.com/SenpaiSeeker/norsodikin"
qr_bytes = await qr_manager.generate(data=teks_atau_url)

qr_file = BytesIO(qr_bytes)
qr_file.name = "qrcode.png"

# await message.reply_photo(qr_file, caption=f"QR Code untuk:\n`{teks_atau_url}`")
```

#### **B. Membaca QR Code dari Gambar**
Metode `read(image_data: bytes)` mengekstrak teks dari gambar QR Code.

**Catatan Instalasi Penting:**
Fitur ini memerlukan pustaka sistem `ZBar`. Jika Anda menggunakan OS berbasis **Debian** atau **Ubuntu**, Anda **wajib** menginstalnya terlebih dahulu dengan perintah:
```bash
sudo apt-get install libzbar0
```
Tanpa pustaka ini, fungsi pembaca QR Code akan gagal.

- **Parameter:** `image_data` (`bytes`): Data gambar mentah.
- **Return:** `str` (teks hasil decode) atau `None` jika gagal.

**Contoh Penggunaan dengan Pyrogram:**
```python
# @app.on_message(filters.command("readqr") | filters.photo)
async def read_qr_handler(client, message):
    target_message = message.reply_to_message or message
    
    if not target_message.photo:
        await message.reply("Mohon balas ke sebuah gambar atau kirim gambar langsung.")
        return

    status_msg = await message.reply("🔍 Memindai QR Code...")
    # Download foto ke memory
    photo_bytes_io = await client.download_media(target_message.photo.file_id, in_memory=True)
    image_data = photo_bytes_io.getvalue()

    # Panggil metode read dari modul
    decoded_text = await qr_manager.read(image_data=image_data)

    if decoded_text:
        await status_msg.edit(f"✅ **QR Code Terbaca:**\n\n`{decoded_text}`")
    else:
        await status_msg.edit("❌ Tidak dapat menemukan QR Code pada gambar ini.")
```

---

### 18. `shell` -> `client.ns.utils.shell`
Eksekutor perintah shell/terminal secara asinkron dari dalam Python. Berguna untuk tugas otomatisasi dan manajemen server.

**Struktur & Return Value:**
Metode `run(command)` mengembalikan tuple yang berisi: (`stdout`, `stderr`, `returncode`).
- `stdout` (`str`): Output standar dari perintah.
- `stderr` (`str`): Output error dari perintah (jika ada).
- `returncode` (`int`): Kode status eksekusi (0 berarti sukses).

**Contoh Penggunaan:**
```python
# Menjalankan perintah 'ls -l'
stdout, stderr, code = await client.ns.utils.shell.run("ls -l /home")

if code == 0:
    # Sukses
    # await message.reply(f"**Hasil `ls -l`:**\n```{stdout}```")
    print(stdout)
else:
    # Gagal
    # await message.reply(f"**Error saat menjalankan perintah:**\n```{stderr}```")
    print(stderr)
```
**Peringatan Keamanan:** Hati-hati saat menjalankan perintah yang berasal dari input pengguna untuk menghindari *shell injection*. Selalu validasi input jika memungkinkan.

---

### 19. `storekey` -> `client.ns.data.key`
Manajer untuk menangani kunci rahasia dan nama file environment dari argumen terminal, mencegah *hardcoding* kredensial.

**1. Cara Menjalankan di Terminal:**
```bash
python3 main.py --key kunci-rahasia-anda --env config.env
```

**2. Cara Menggunakan di Kode Python:**
```python
# Di file main.py Anda
key_manager = client.ns.data.key()
try:
    # Fungsi ini akan membaca argumen dari terminal
    kunci_rahasia, nama_file_env = key_manager.handle_arguments()
    
    print(f"Menggunakan Kunci: {kunci_rahasia}")
    print(f"File Environment: {nama_file_env}")
    
    # Gunakan variabel ini untuk setup selanjutnya, misal load env file
    # from dotenv import load_dotenv
    # load_dotenv(nama_file_env)
    
except SystemExit:
    # Skrip akan berhenti jika argumen tidak lengkap
    print("Skrip dihentikan karena argumen --key dan --env wajib diisi.")

```
---

### 20. `translate` -> `client.ns.ai.translate`
Modul AI untuk menerjemahkan teks ke berbagai bahasa menggunakan Google Translate API.

**Struktur & Inisialisasi:**
Kelas `Translator` tidak memerlukan parameter saat inisialisasi.

**Metode Utama & Parameter:**
- `to(text: str, dest_lang: str = 'en')`
  - `text`: Teks yang ingin diterjemahkan.
  - `dest_lang`: Kode bahasa tujuan (misal: 'en' untuk Inggris, 'ja' untuk Jepang, 'id' untuk Indonesia). Default-nya adalah 'en'.

**Contoh Penggunaan:**
```python
translator = client.ns.ai.translate()

# Terjemahkan dari Indonesia ke Inggris
teks_id = "Selamat pagi, bagaimana kabarmu?"
hasil_en = await translator.to(teks_id, dest_lang="en")
print(f"'{teks_id}' -> '{hasil_en}'")

# Terjemahkan dari Inggris ke Jepang
teks_en = "Artificial intelligence will change the world."
hasil_ja = await translator.to(teks_en, dest_lang="ja")
print(f"'{teks_en}' -> '{hasil_ja}'")
```

---

### 21. `tts` -> `client.ns.ai.tts`
Modul AI untuk mengubah teks menjadi pesan suara (Text-to-Speech) menggunakan API Google.

**Struktur & Inisialisasi:**
Kelas ini tidak memerlukan parameter saat inisialisasi.

**Contoh Penggunaan:**
```python
from io import BytesIO

tts_generator = client.ns.ai.tts()
audio_bytes = await tts_generator.generate(
    text="Halo, ini adalah pesan suara yang dibuat secara otomatis oleh Norsodikin.", 
    lang="id" # Kode bahasa (opsional, default 'id')
)

file_suara = BytesIO(audio_bytes)
file_suara.name = "notifikasi.ogg" # Nama file penting untuk Telegram
# await message.reply_voice(file_suara, caption="Pesan Suara Penting!")
```

---

### 22. `url` -> `client.ns.utils.url`
Utilitas sederhana untuk memendekkan URL menggunakan layanan TinyURL.

**Struktur & Inisialisasi:**
Kelas `UrlUtils` tidak memerlukan parameter saat inisialisasi.

**Metode Utama & Parameter:**
- `shorten(long_url: str)`
  - `long_url`: URL panjang yang ingin Anda perpendek.

**Contoh Penggunaan:**
```python
url_panjang = "https://github.com/SenpaiSeeker/norsodikin/blob/main/README.md"
url_pendek = await client.ns.utils.url.shorten(url_panjang)

print(f"URL Panjang: {url_panjang}")
print(f"URL Pendek: {url_pendek}")
# await message.reply(f"URL telah dipendekkan: {url_pendek}")
```

---

### 23. `web` -> `client.ns.ai.web`
Alat AI canggih untuk melakukan *scraping* konten teks dari sebuah URL dan merangkumnya menggunakan model Gemini.

**Struktur & Inisialisasi:**
**Penting:** Kelas ini *harus* diinisialisasi dengan sebuah instance dari `gemini` yang sudah dibuat sebelumnya.
```python
# 1. Buat instance Gemini terlebih dahulu
gemini_bot = client.ns.ai.gemini(api_key="GEMINI_API_KEY_ANDA")

# 2. Berikan instance tersebut saat membuat WebSummarizer
web_summarizer = client.ns.ai.web(gemini_instance=gemini_bot)
```

**Contoh Penggunaan:**
```python
url_berita = "https://www.kompas.com/global/read/2023/12/13/165507970/apa-itu-kecerdasan-buatan-pengertian-dan-contohnya"
status_msg = await message.reply("⏳ Sedang membaca dan merangkum artikel...")

try:
    # Parameter max_length bersifat opsional, default 8000 karakter
    # Berguna untuk menghemat token jika artikel sangat panjang
    rangkuman = await web_summarizer.summarize(url_berita, max_length=5000)

    # Tampilkan hasilnya
    # await status_msg.edit(f"📄 **Rangkuman Artikel:**\n\n{rangkuman}")
except Exception as e:
    # await status_msg.edit(f"Gagal merangkum: {e}")
```

---

### 24. `ymlreder` -> `client.ns.data.yaml`
Utilitas praktis untuk membaca file konfigurasi `.yml` dan mengubahnya menjadi objek Python yang bisa diakses dengan notasi titik (`.`).

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
    
    # Bekerja dengan list of objects
    for api in config.api_keys:
        if api.name == "google":
            print(f"Kunci API Google ditemukan: {api.key}")
else:
    print("Gagal memuat file konfigurasi.")
```
---
</details>

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, kamu bebas pakai, modifikasi, dan distribusikan untuk proyek apa pun.

---

Semoga dokumentasi ini bikin kamu makin semangat ngoding! Selamat mencoba dan berkreasi dengan `norsodikin`. Jika ada pertanyaan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
