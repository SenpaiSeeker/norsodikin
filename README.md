# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`, sebuah koleksi modul Python serbaguna yang dirancang untuk mempermudah berbagai tugas, mulai dari manajemen server, enkripsi data, hingga pembuatan bot Telegram yang canggih.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas dapat diakses secara intuitif melalui `client.ns`, membuat kode bot Anda lebih bersih dan rapi.

## Instalasi

Untuk menginstal pustaka ini, cukup jalankan perintah berikut di terminal Anda:

```bash
pip install norsodikin pyrogram 
```

Pastikan juga semua dependensi dari file `requirements.txt` sudah terpasang jika Anda menginstal dari source code.

## Cara Penggunaan Terintegrasi dengan Pyrogram

Cukup dengan mengimpor `nsdev`, semua fungsionalitas akan otomatis "melekat" pada objek `client` Pyrogram Anda melalui namespace `ns`.

**Struktur Dasar**:

```python
import pyrogram
import nsdev  # Mengaktifkan integrasi .ns

# Asumsikan 'client' adalah instance dari pyrogram.Client
# client = pyrogram.Client(...)

# Sekarang Anda bisa mengakses semua modul:
# client.ns.log.info("Ini adalah logger.")
# db = client.ns.db(storage_type="local")
# ...dan seterusnya
```

Berikut adalah panduan lengkap untuk setiap modul yang tersedia di dalam `client.ns`.

---

### 1. `nsdev.addUser` - Manajemen Pengguna SSH

Sangat berguna untuk mengelola pengguna di server Linux. Dengan `client.ns.user`, Anda bisa menambah dan menghapus pengguna SSH, lalu mengirim detailnya langsung ke Telegram.

**Cara Penggunaan:**

```python
# Inisialisasi dengan token bot Telegram dan chat ID tujuan
# (Token & ID di bawah ini hanya contoh, ganti dengan milikmu)
manager = client.ns.user(bot_token="TOKEN_BOT_ANDA", chat_id=ID_CHAT_ANDA)

# 1. Menambahkan pengguna baru dengan username & password acak
print("Menambahkan pengguna baru...")
manager.add_user()
# Info login akan otomatis dikirim ke Telegram

# 2. Menambahkan pengguna baru dengan username & password spesifik
print("Menambahkan pengguna 'budi'...")
manager.add_user(ssh_username="budi", ssh_password="password123")

# 3. Menghapus pengguna
print("Menghapus pengguna 'budi'...")
manager.delete_user(ssh_username="budi")
```
**Catatan:** Skrip ini memerlukan hak akses `sudo` untuk menjalankan `adduser` dan `deluser`.

---

### 2. `nsdev.argument` - Asisten Argumen Pyrogram

Kumpulan fungsi praktis untuk mem-parsing pesan, mendapatkan info pengguna, dan memeriksa status admin, kini tersedia langsung di `client.ns.arg`.

**Cara Penggunaan (dalam handler Pyrogram):**

```python
# Misal pesan yang diterima: /kick @username alasannya
# Atau membalas pesan seseorang dengan: /kick alasannya

# Mendapatkan user ID dan alasan dari sebuah pesan
user_id, reason = await client.ns.arg.getReasonAndId(message)
print(f"User ID: {user_id}, Alasan: {reason}")

# Mendapatkan teks dari pesan (argumen setelah command)
query = client.ns.arg.getMessage(message, is_arg=True)
print(f"Query: {query}")

# Membuat tag mention HTML untuk pengguna
me = await client.get_me()
mention = client.ns.arg.getMention(me) # -> <a href='tg://user?id=...'>Nama Depan</a>
print(mention)

# Cek apakah pengguna adalah admin
is_admin = await client.ns.arg.getAdmin(message)
print(f"Apakah user seorang admin? {is_admin}")
```

---

### 3. `nsdev.bing` - Pembuat Gambar AI (Bing)

Hasilkan gambar keren dari teks menggunakan Bing Image Creator. Anda hanya perlu memberikan *cookie* otentikasi. Akses melalui `client.ns.bing`.

**Cara Penggunaan:**

```python
import asyncio

# Anda harus login ke bing.com di browser, lalu salin nilai cookie.
BING_AUTH_COOKIE_U = "COOKIE_U_ANDA"
BING_AUTH_COOKIE_SRCHHPGUSR = "COOKIE_SRCHHPGUSR_ANDA"

async def main():
    # Inisialisasi generator
    bing_image_gen = client.ns.bing(
        auth_cookie_u=BING_AUTH_COOKIE_U,
        auth_cookie_srchhpgusr=BING_AUTH_COOKIE_SRCHHPGUSR
    )
    
    prompt = "seekor rubah cyberpunk mengendarai motor di kota neon"
    print(f"Membuat gambar dengan prompt: '{prompt}'...")
    
    image_urls = await bing_image_gen.generate(prompt=prompt, num_images=4)
    print(f"URL Gambar: {image_urls}")

# Jalankan dalam event loop (Pyrogram sudah melakukannya untuk Anda di handler)
```

---

### 4. `nsdev.button` - Pembuat Tombol Keren untuk Telegram

Sederhanakan pembuatan tombol *inline* atau *reply* dengan `client.ns.button` menggunakan sintaks berbasis teks.

**Cara Penggunaan:**

```python
# 1. Membuat Keyboard Inline
# Syntax: | Teks Tombol - data_callback_atau_url |
# Modifier 'same' untuk menempatkan di baris yang sama.
text_with_buttons = """
Ini adalah pesan dengan tombol. Pilih salah satu:
| Tombol 1 - data1 |
| Tombol 2 - data2 |
| Google - https://google.com | | Bantuan - help;same |
"""

# Parsing teks untuk membuat keyboard dan mendapatkan teks sisanya
inline_keyboard, remaining_text = client.ns.button.create_keyboard(text_with_buttons)
await message.reply(remaining_text, reply_markup=inline_keyboard)

# 2. Membuat Keyboard Reply (tombol di bawah area ketik)
text_with_reply = """
Halo! Pilih menu di bawah.
| Menu Utama - Tentang Kami - Kontak;same |
"""

reply_keyboard, remaining_text_reply = client.ns.button.create_reply_keyboard(text_with_reply)
await message.reply(remaining_text_reply, reply_markup=reply_keyboard)
```

---

### 5. `nsdev.colorize` - Pewarna Teks Terminal

Berikan warna-warni pada output terminal skrip Anda dengan `client.ns.color`.

**Cara Penggunaan:**

```python
colors = client.ns.color

print(f"{colors.GREEN}Pesan ini berwarna hijau!{colors.RESET}")
print(f"{colors.RED}Peringatan: Ada kesalahan!{colors.RESET}")
print(f"{colors.CYAN}Ini adalah informasi penting.{colors.RESET}")

# Cetak semua warna yang tersedia
colors.print_all_colors()
```

---

### 6. `nsdev.database` - Database Serbaguna dengan Enkripsi

`client.ns.db` adalah solusi penyimpanan data fleksibel (JSON, MongoDB, SQLite) dengan enkripsi otomatis.

**Cara Penggunaan:**

```python
# --- Menggunakan file JSON local (paling simpel) ---
# Inisialisasi (file 'my_database.json' akan dibuat)
db = client.ns.db(storage_type="local", file_name="my_database")

# Simpan variabel untuk user_id tertentu
user_id = 12345
db.setVars(user_id, "NAMA", "Budi")
db.setVars(user_id, "LEVEL", 10)

# Ambil variabel
nama = db.getVars(user_id, "NAMA")
print(f"Nama Pengguna: {nama}") # Output: Budi

# Atur tanggal kedaluwarsa (30 hari dari sekarang)
db.setExp(user_id, exp=30)
print(f"Sisa hari: {db.daysLeft(user_id)}")

# Tutup koneksi saat selesai (penting untuk SQLite)
db.close()

# --- Contoh inisialisasi lain ---
# db_mongo = client.ns.db(storage_type="mongo", mongo_url="...")
# db_sqlite = client.ns.db(storage_type="sqlite", file_name="data.db")
```

---

### 7. `nsdev.encrypt` - Enkripsi dan Dekripsi Sederhana

Butuh cara cepat untuk menyamarkan data? Gunakan `client.ns.encrypt` yang menyediakan beberapa metode enkripsi sederhana.

**Cara Penggunaan:**

```python
# Inisialisasi dengan metode 'bytes' dan sebuah kunci (angka)
# Akses kelas CipherHandler melalui namespace `encrypt`
cipher = client.ns.code.Cipher(method="bytes", key=123456789)

# Teks asli
pesan_rahasia = "Ini adalah pesan yang sangat rahasia."

# Enkripsi
encrypted_text = cipher.encrypt(pesan_rahasia)
print(f"Teks Terenkripsi: {encrypted_text}")

# Dekripsi
decrypted_text = cipher.decrypt(encrypted_text)
print(f"Teks Asli: {decrypted_text}")
```

---

### 8. `nsdev.gemini` - Ngobrol dengan AI Google Gemini

Berinteraksi dengan model AI Gemini dari Google. Cocok untuk chatbot atau mode hiburan "cek khodam". Akses melalui `client.ns.gemini`.

**Cara Penggunaan:**

```python
# Ganti dengan API Key kamu dari Google AI Studio
GEMINI_API_KEY = "API_KEY_ANDA"
chatbot = client.ns.gemini(api_key=GEMINI_API_KEY)
user_id = 12345 # ID unik untuk setiap pengguna

# 1. Mode Chatbot Santai
pertanyaan = "kasih aku jokes bapak-bapak dong"
jawaban = chatbot.send_chat_message(pertanyaan, user_id=user_id, bot_name="BotKeren")
print(f"Jawaban Bot: {jawaban}")

# 2. Mode Cek Khodam (untuk hiburan)
nama = "Nor Sodikin"
user_id = 12345
deskripsi_khodam = chatbot.send_khodam_message(nama, user_id=user_id)
print(f"\n--- Hasil Cek Khodam untuk {nama} ---\n{deskripsi_khodam}")
```

---

### 9. `nsdev.gradient` - Efek Teks Keren di Terminal

Hidupkan tampilan terminal dengan banner teks bergradien dan *countdown timer* animatif menggunakan `client.ns.grad`.

**Cara Penggunaan:**

```python
import asyncio

# 1. Render teks dengan efek gradien
client.ns.grad.render_text("Nor Sodikin")

# 2. Countdown timer animatif
async def run_countdown():
    print("\nMemulai hitung mundur...")
    await client.ns.grad.countdown(10, text="Harap tunggu {time} lagi...")
    print("\nWaktu habis!")

# asyncio.run(run_countdown())
```

---

### 10. `nsdev.logger` - Pencatat Log Informatif dan Berwarna

`client.ns.log` adalah versi canggih dari `print()`. Mencatat pesan ke konsol dengan format rapi, berwarna, lengkap dengan waktu, file, dan nama fungsi.

**Cara Penggunaan (dalam fungsi apapun):**

```python
def fungsi_penting():
    client.ns.log.info("Memulai proses penting.")
    try:
        a = 10 / 0
    except Exception as e:
        client.ns.log.error(f"Terjadi kesalahan: {e}")
    client.ns.log.warning("Proses mungkin tidak berjalan sempurna.")
    client.ns.log.debug("Nilai variabel saat ini: ...")

fungsi_penting()
# Output di konsol akan terlihat sangat rapi dan berwarna!
```

---

### 11. `nsdev.payment` - Integrasi Payment Gateway

Butuh sistem pembayaran? Gunakan `client.ns.payment` yang menyediakan klien untuk Midtrans, Tripay, dan VioletMediaPay.

**Cara Penggunaan (Contoh dengan VioletMediaPay):**

```python
import asyncio

VIOLET_API_KEY = "API_KEY_ANDA"
VIOLET_SECRET_KEY = "SECRET_KEY_ANDA"

async def buat_pembayaran():
    # Akses kelas melalui namespace 'payment'
    # 'live=False' untuk mode sandbox/testing
    payment_client = client.ns.payment.Violet(
        api_key=VIOLET_API_KEY, secret_key=VIOLET_SECRET_KEY, live=False
    )
    
    payment = await payment_client.create_payment(
        channel_payment="QRIS", amount="5000", produk="Donasi Kopi"
    )

    if payment.api_response.status:
        print(f"QR Code Link: {payment.api_response.data.target}")
    else:
        print(f"Gagal: {payment.api_response.data.status}")
            
# asyncio.run(buat_pembayaran())
```
*Untuk `Midtrans` dan `Tripay`, akses melalui `client.ns.payment.Midtrans` dan `client.ns.payment.Tripay`.*

---

### 12. `nsdev.storekey` - Penyimpanan Kunci yang Aman

`client.ns.key` berfungsi seperti "brankas kecil" untuk menyimpan data sensitif (kunci API) secara terenkripsi di file sementara.

**Cara Penggunaan (di awal skrip Anda):**

```python
# Inisialisasi KeyManager
key_manager = client.ns.key(filename="kunci_aplikasi.json")

# Panggil fungsi ini di awal skrip.
# Jika file kunci belum ada, pengguna akan diminta untuk memasukkannya.
# Jika sudah ada, fungsi ini akan membacanya dari file.
kunci, nama_env = key_manager.handle_arguments()

print(f"Kunci yang digunakan: {kunci}")
print(f"Nama Environment: {nama_env}")

# Juga bisa diatur via command line:
# python skrip_kamu.py --key 12345 --env .env_development
```

---

### 13. `nsdev.ymlreder` - Pembaca File YAML Praktis

`client.ns.yaml` membuat pekerjaan dengan file konfigurasi `.yml` sangat mudah, mengubahnya menjadi objek Python yang bisa diakses dengan notasi titik.

**Cara Penggunaan:**

Anggap kamu punya file `config.yml` seperti contoh di awal.

```python
# Muat file dan ubah menjadi objek
config = client.ns.yaml.loadAndConvert("config.yml")

if config:
    # Akses data dengan mudah
    db_host = config.database.host
    db_port = config.database.port
    print(f"Host Database: {db_host}:{db_port}")
    
    # Akses list
    for api in config.api_keys:
        print(f"API {api.name} key: {api.key}")
```

## Penggunaan Standalone (Tanpa Pyrogram)

Jika Anda ingin menggunakan modul ini di luar proyek bot Pyrogram, Anda tetap bisa mengimpornya secara langsung seperti pustaka Python biasa.

```python
from nsdev import DataBase
from nsdev import AnsiColors

# ...dan seterusnya
```

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Kamu bebas menggunakan, memodifikasi, dan mendistribusikannya.

---

Semoga dokumentasi baru ini membantu Anda berkreasi lebih cepat dan efisien! Selamat mencoba dengan [norsodikin](https://t.me/NorSodikin).
