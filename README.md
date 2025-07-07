# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`, sebuah koleksi modul Python serbaguna yang dirancang untuk mempermudah berbagai tugas, mulai dari manajemen server, enkripsi data, hingga pembuatan bot Telegram yang canggih. Setiap modul dibuat agar mudah digunakan dan dipahami, bahkan untuk kamu yang baru mulai belajar.

## Instalasi

Untuk menginstal pustaka ini, cukup jalankan perintah berikut di terminal kamu:

```bash
pip install norsodikin
```

Pastikan juga semua dependensi dari file `requirements.txt` sudah terpasang.

## Panduan Penggunaan Modul

Berikut adalah panduan lengkap untuk setiap modul yang tersedia di dalam `nsdev`.

---

### 1. `nsdev.addUser` - Manajemen Pengguna SSH

Modul ini sangat berguna jika kamu sering mengelola pengguna di server Linux. Dengan `SSHUserManager`, kamu bisa menambah dan menghapus pengguna SSH secara otomatis, lalu mengirimkan detail loginnya langsung ke Telegram.

**Cara Penggunaan:**

```python
from nsdev.addUser import SSHUserManager

# Inisialisasi dengan token bot Telegram dan chat ID tujuan
# (Token & ID di bawah ini hanya contoh, ganti dengan milikmu)
manager = SSHUserManager(bot_token="TOKEN_BOT_ANDA", chat_id=ID_CHAT_ANDA)

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

**Catatan:** Skrip ini memerlukan hak akses `sudo` untuk menjalankan perintah `adduser` dan `deluser`.

---

### 2. `nsdev.argument` - Asisten Argumen Pyrogram

Jika kamu membangun bot Telegram dengan `Pyrogram`, modul ini adalah teman terbaikmu. Isinya adalah kumpulan fungsi praktis untuk mem-parsing pesan, mendapatkan info pengguna, dan memeriksa status admin dengan lebih mudah.

**Cara Penggunaan:**

```python
from nsdev.argument import Argument

# Asumsikan kita punya objek 'message' dari Pyrogram
# dan 'client' dari Pyrogram
arg_handler = Argument()

# --- Contoh Penggunaan (harus dijalankan di dalam event handler Pyrogram) ---

# Misal pesan yang diterima adalah: /kick @username alasannya
# Atau membalas pesan seseorang dengan: /kick alasannya

# Mendapatkan user ID dan alasan dari sebuah pesan
# user_id, reason = await arg_handler.getReasonAndId(message)
# print(f"User ID: {user_id}, Alasan: {reason}")

# Mendapatkan teks dari pesan (argumen setelah command)
# query = arg_handler.getMessage(message, is_arg=True)
# print(f"Query: {query}")

# Membuat tag mention HTML untuk pengguna
# me = await client.get_me()
# mention = arg_handler.getMention(me) # -> <a href='tg://user?id=...'>Nama Depan</a>
# print(mention)

# Cek apakah pengguna adalah admin
# is_admin = await arg_handler.getAdmin(message)
# print(f"Apakah user seorang admin? {is_admin}")
```

---

### 3. `nsdev.bing` - Pembuat Gambar AI (Bing)

Ingin membuat gambar keren dari teks menggunakan AI? Modul ini terhubung dengan Bing Image Creator. Kamu hanya perlu memberikan *cookie* otentikasi dari akun Bing-mu.

**Cara Penggunaan:**

```python
import asyncio
from nsdev.bing import ImageGenerator

# Kamu harus login ke bing.com terlebih dahulu di browser,
# lalu salin nilai cookie _U dan SRCHHPGUSR dari sana.
BING_AUTH_COOKIE_U = "COOKIE_U_ANDA"
BING_AUTH_COOKIE_SRCHHPGUSR = "COOKIE_SRCHHPGUSR_ANDA"

async def main():
    try:
        # Inisialisasi generator
        bing_image_gen = ImageGenerator(
            auth_cookie_u=BING_AUTH_COOKIE_U,
            auth_cookie_srchhpgusr=BING_AUTH_COOKIE_SRCHHPGUSR
        )
        
        prompt = "seekor rubah cyberpunk mengendarai motor di kota neon"
        print(f"Membuat gambar dengan prompt: '{prompt}'...")

        # Hasilkan 4 gambar
        image_urls = await bing_image_gen.generate(prompt=prompt, num_images=4)

        if image_urls:
            print("\nBerhasil! Berikut adalah URL gambar:")
            for i, url in enumerate(image_urls):
                print(f"{i+1}. {url}")
        else:
            print("Gagal membuat gambar.")

    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

# Jalankan fungsi async
asyncio.run(main())
```

---

### 4. `nsdev.button` - Pembuat Tombol Keren untuk Telegram

Membuat tombol *inline* atau *reply* di bot Telegram bisa jadi merepotkan. Modul `Button` menyederhanakannya dengan sintaks berbasis teks yang unik.

**Cara Penggunaan:**

```python
from nsdev.button import Button

button_builder = Button()

# 1. Membuat Keyboard Inline
# Sintaks: | Teks Tombol - data_callback_atau_url |
# Modifiers:
# - 'same': Menempatkan tombol di baris yang sama dengan tombol sebelumnya.

text_with_buttons = """
Ini adalah pesan dengan tombol inline.
Pilih salah satu:
| Tombol 1 - data1 |
| Tombol 2 - data2 |
| Google - https://google.com | | Bantuan - help;same |
"""

# Parsing teks untuk membuat keyboard dan mendapatkan teks sisanya
inline_keyboard, remaining_text = button_builder.create_keyboard(text_with_buttons)

print("Teks Pesan:", remaining_text)
print("Markup Keyboard Inline:", inline_keyboard)

# 2. Membuat Keyboard Reply (tombol di bawah area ketik)
# Sintaks: | tombol 1 - tombol 2 |

text_with_reply = """
Halo! Pilih menu di bawah.
| Menu Utama - Tentang Kami - Kontak;same |
"""

reply_keyboard, remaining_text_reply = button_builder.create_reply_keyboard(text_with_reply)

print("\nTeks Pesan (Reply):", remaining_text_reply)
print("Markup Keyboard Reply:", reply_keyboard)
```

---

### 5. `nsdev.colorize` - Pewarna Teks Terminal

Bosan dengan terminal yang monoton? Gunakan `AnsiColors` untuk memberikan sentuhan warna-warni pada output skrip kamu.

**Cara Penggunaan:**

```python
from nsdev.colorize import AnsiColors

colors = AnsiColors()

print(f"{colors.GREEN}Pesan ini berwarna hijau!{colors.RESET}")
print(f"{colors.RED}Peringatan: Ada kesalahan!{colors.RESET}")
print(f"{colors.CYAN}Ini adalah informasi penting.{colors.RESET}")

# Cetak semua warna yang tersedia
colors.print_all_colors()

# Dapatkan kode warna acak
random_code, reset_code = colors.random_color()
print(f"{random_code}Teks ini warnanya acak!{reset_code}")
```

---

### 6. `nsdev.database` - Database Serbaguna dengan Enkripsi

`DataBase` adalah solusi penyimpanan data yang fleksibel dan aman. Kamu bisa memilih tiga jenis penyimpanan: file JSON lokal, MongoDB, atau SQLite. Semua data sensitif dienkripsi secara otomatis.

**Cara Penggunaan:**

```python
# --- 1. Menggunakan file JSON lokal (paling simpel) ---
from nsdev.database import DataBase

# Inisialisasi (file 'my_database.json' akan dibuat)
db = DataBase(storage_type="local", file_name="my_database")

# Simpan variabel untuk user_id tertentu
user_id = 12345
db.setVars(user_id, "NAMA", "Budi")
db.setVars(user_id, "LEVEL", 10)

# Ambil variabel
nama = db.getVars(user_id, "NAMA")
print(f"Nama Pengguna: {nama}") # Output: Budi

# Tambahkan item ke dalam list
db.setListVars(user_id, "HOBI", "Membaca")
db.setListVars(user_id, "HOBI", "Memancing")

# Ambil list
hobi = db.getListVars(user_id, "HOBI")
print(f"Hobi: {hobi}") # Output: ['Membaca', 'Memancing']

# Atur tanggal kedaluwarsa (30 hari dari sekarang)
db.setExp(user_id, exp=30)
print(f"Tanggal kedaluwarsa: {db.getExp(user_id)}")
print(f"Sisa hari: {db.daysLeft(user_id)}")

db.close()

# --- 2. Menggunakan MongoDB ---
# db_mongo = DataBase(storage_type="mongo", mongo_url="MONGO_URL_ANDA", file_name="nama_db")

# --- 3. Menggunakan SQLite ---
# db_sqlite = DataBase(storage_type="sqlite", file_name="data_sqlite")
```

---

### 7. `nsdev.encrypt` - Enkripsi dan Dekripsi Sederhana

Butuh cara cepat untuk menyamarkan data? `CipherHandler` menyediakan beberapa metode enkripsi sederhana yang cocok untuk menyembunyikan konfigurasi atau teks biasa.

**Cara Penggunaan:**

```python
from nsdev.encrypt import CipherHandler

# Inisialisasi dengan metode 'bytes' dan sebuah kunci (angka)
cipher = CipherHandler(method="bytes", key=123456789)

# Teks asli
pesan_rahasia = "Ini adalah pesan yang sangat rahasia."

# Enkripsi
encrypted_text = cipher.encrypt(pesan_rahasia)
print(f"Teks Terenkripsi:\n{encrypted_text}")

# Dekripsi
decrypted_text = cipher.decrypt(encrypted_text)
print(f"\nTeks Asli setelah Dekripsi:\n{decrypted_text}")

# Kamu juga bisa menyimpan kode Python dalam bentuk terenkripsi
# cipher.save("skrip_rahasia.py", "print('Halo dari skrip rahasia!')")
```

---

### 8. `nsdev.gemini` - Ngobrol dengan AI Google Gemini

Modul ini adalah jembatan untuk berinteraksi dengan model AI canggih dari Google, yaitu Gemini. Kamu bisa menggunakannya untuk chatbot umum atau mode "cek khodam" yang unik.

**Cara Penggunaan:**

```python
from nsdev.gemini import ChatbotGemini

# Ganti dengan API Key kamu dari Google AI Studio
GEMINI_API_KEY = "API_KEY_ANDA"
chatbot = ChatbotGemini(api_key=GEMINI_API_KEY)
user_id = 12345 # ID unik untuk setiap pengguna agar riwayat chat tidak tercampur

# 1. Mode Chatbot Santai
pertanyaan = "kasih aku jokes bapak-bapak dong"
jawaban = chatbot.send_chat_message(pertanyaan, user_id=user_id, bot_name="BotKeren")
print(f"Jawaban Bot:\n{jawaban}")

# 2. Mode Cek Khodam (untuk hiburan)
nama = "Nor Sodikin"
deskripsi_khodam = chatbot.send_khodam_message(nama)
print(f"\n--- Hasil Cek Khodam untuk {nama} ---")
print(deskripsi_khodam)
```

---

### 9. `nsdev.gradient` - Efek Teks Keren di Terminal

Jadikan tampilan terminalmu lebih hidup! `Gradient` bisa membuat banner teks dengan warna gradien yang indah dan menampilkan *countdown timer* yang animatif.

**Cara Penggunaan:**

```python
import asyncio
from nsdev.gradient import Gradient

gradient_effect = Gradient()

# 1. Render teks dengan efek gradien
gradient_effect.render_text("Nor Sodikin")

# 2. Countdown timer animatif
async def run_countdown():
    print("\nMemulai hitung mundur...")
    await gradient_effect.countdown(10, text="Harap tunggu {time} lagi...")
    print("\nWaktu habis!")

asyncio.run(run_countdown())
```

---

### 10. `nsdev.logger` - Pencatat Log yang Informatif dan Berwarna

`LoggerHandler` adalah versi canggih dari `print()`. Ini akan mencatat pesan ke konsol dengan format yang rapi, lengkap dengan waktu, nama file, fungsi, dan level log yang berwarna.

**Cara Penggunaan:**

```python
from nsdev.logger import LoggerHandler

# Inisialisasi logger
log = LoggerHandler()

def fungsi_penting():
    log.info("Memulai proses penting.")
    try:
        a = 10 / 0
    except Exception as e:
        log.error(f"Terjadi kesalahan: {e}")
    log.warning("Proses mungkin tidak berjalan sempurna.")
    log.debug("Nilai variabel saat ini: ...")

fungsi_penting()
# Output di konsol akan terlihat sangat rapi dan berwarna!
```

---

### 11. `nsdev.payment` - Integrasi Payment Gateway

Butuh sistem pembayaran di aplikasimu? Modul ini menyediakan klien untuk tiga *payment gateway* populer di Indonesia: Midtrans, Tripay, dan VioletMediaPay.

**Cara Penggunaan (Contoh dengan `VioletMediaPayClient`):**

```python
import asyncio
from nsdev.payment import VioletMediaPayClient

VIOLET_API_KEY = "API_KEY_ANDA"
VIOLET_SECRET_KEY = "SECRET_KEY_ANDA"

async def buat_pembayaran():
    # Inisialisasi klien (live=False untuk mode sandbox/testing)
    client = VioletMediaPayClient(api_key=VIOLET_API_KEY, secret_key=VIOLET_SECRET_KEY, live=False)
    
    try:
        print("Membuat link pembayaran QRIS sebesar Rp 5.000...")
        payment = await client.create_payment(
            channel_payment="QRIS",
            amount="5000",
            produk="Donasi Kopi"
        )

        if payment.api_response.success:
            print("\nBerhasil! Detail Pembayaran:")
            print(f"  - QR Code Link: {payment.api_response.data.qrcode_url}")
            print(f"  - Bayar Sebelum: {payment.api_response.data.expired_time_format}")
            print(f"  - Kode Referensi: {payment.ref_kode}")
        else:
            print(f"Gagal: {payment.api_response.message}")
            
    except Exception as e:
        print(f"Terjadi error: {e}")

asyncio.run(buat_pembayaran())
```

*Untuk `PaymentMidtrans` dan `PaymentTripay`, cara penggunaannya serupa. Cukup inisialisasi dengan kunci API masing-masing dan panggil metode yang relevan.*

---

### 12. `nsdev.storekey` - Penyimpanan Kunci yang Aman

Modul ini berfungsi seperti "brankas kecil" untuk menyimpan data sensitif (seperti kunci API) di file sementara. Data tersebut akan dienkripsi sebelum disimpan, jadi lebih aman daripada menyimpannya sebagai teks biasa.

**Cara Penggunaan:**

`KeyManager` biasanya digunakan dalam skrip yang dijalankan dari terminal.

```python
# Di dalam skrip Python kamu
from nsdev.storekey import KeyManager

key_manager = KeyManager(filename="kunci_aplikasi.json")

# Panggil fungsi ini di awal skrip
# Jika file kunci belum ada, pengguna akan diminta untuk memasukkannya.
# Jika sudah ada, fungsi ini akan membacanya dari file.
kunci, nama_env = key_manager.handle_arguments()

print(f"Kunci yang digunakan: {kunci}")
print(f"Nama Environment: {nama_env}")
```

Kamu juga bisa mengatur kuncinya langsung dari *command line*:
`python skrip_kamu.py --key 12345 --env .env_development`

---

### 13. `nsdev.ymlreder` - Pembaca File YAML yang Praktis

`YamlHandler` (ya, ada typo di nama filenya, tapi fungsionalitasnya tetap keren!) membuat pekerjaan dengan file konfigurasi `.yml` menjadi sangat mudah. Ia akan mengubah file YAML menjadi objek Python, sehingga kamu bisa mengakses nilainya dengan notasi titik (`.`).

**Cara Penggunaan:**

Anggap kamu punya file `config.yml` seperti ini:
```yml
database:
  host: "localhost"
  port: 5432
  user: "admin"

api_keys:
  - name: "google"
    key: "xyz-123"
  - name: "telegram"
    key: "abc-456"
```

Lalu di Python:
```python
from nsdev.ymlreder import YamlHandler

reader = YamlHandler()

# Muat file dan ubah menjadi objek
config = reader.loadAndConvert("config.yml")

if config:
    # Akses data dengan mudah
    db_host = config.database.host
    db_port = config.database.port
    
    print(f"Host Database: {db_host}")
    print(f"Port Database: {db_port}")
    
    # Akses list
    for api in config.api_keys:
        print(f"API {api.name} memiliki kunci: {api.key}")
```

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Kamu bebas menggunakan, memodifikasi, dan mendistribusikannya.

---

Semoga dokumentasi ini membantumu! Selamat mencoba dan berkreasi dengan [norsodikin](https://t.me/NorSodikin).
