# Norsodikin Dev (`nsdev`)

[![PyPI version](https://badge.fury.io/py/norsodikin.svg)](https://badge.fury.io/py/norsodikin)

Sebuah pustaka Python serbaguna yang dirancang untuk berbagai tugas pengembangan. Pustaka ini mencakup kumpulan alat mulai dari enkripsi data, penataan terminal, integrasi gateway pembayaran, chatbot berbasis AI, hingga utilitas untuk bot Pyrogram.

## Instalasi

Instal paket langsung dari PyPI:

```bash
pip install norsodikin
```

## Daftar Isi

- [AnsiColors](#ansicolors) - Untuk output terminal yang berwarna.
- [Argument](#argument) - Helper untuk mem-parsing argumen di Pyrogram.
- [Button](#button) - Membuat keyboard Pyrogram dari markup teks sederhana.
- [CipherHandler & AsciiManager](#cipherhandler--asciimanager) - Enkripsi dan dekripsi data.
- [DataBase](#database) - Handler database fleksibel dengan enkripsi bawaan.
- [Chatbot Gemini](#chatbot-gemini) - Berinteraksi dengan API Gemini dari Google.
- [Gradient](#gradient) - Membuat teks gradien dan animasi indah di terminal.
- [ImageGenerator (Bing)](#imagegenerator-bing) - Membuat gambar menggunakan DALL-E 3 dari Bing.
- [KeyManager](#keymanager) - Menyimpan dan mengambil kunci sensitif dengan aman.
- [LoggerHandler](#loggerhandler) - Utilitas logging yang kuat dan berwarna.
- [Gateway Pembayaran](#gateway-pembayaran) - Integrasi dengan Midtrans, Tripay, dan VioletMediaPay.
- [Manajer Pengguna SSH](#manajer-pengguna-ssh) - Mengelola pengguna SSH di sistem Linux.
- [YamlHandler](#yamlhandler) - Memuat file YAML sebagai objek Python yang mudah digunakan.

---

## AnsiColors

Kelas sederhana untuk menambahkan warna pada output terminal Anda.

```python
from nsdev import AnsiColors

colors = AnsiColors()

print(f"{colors.GREEN}Ini adalah teks berwarna hijau.{colors.RESET}")
print(f"{colors.LIGHT_BLUE}Ini adalah teks biru muda.{colors.RESET}")
print(f"{colors.ORANGE}Dan ini oranye!{colors.RESET}")

# Cetak semua warna yang tersedia
# colors.print_all_colors()
```

## Argument

Kumpulan fungsi helper untuk mem-parsing pesan dan info pengguna di dalam bot [Pyrogram](https://pyrogram.org/).

```python
from nsdev import Argument
# Asumsikan 'message' adalah objek pesan Pyrogram

arg_handler = Argument()

# Dapatkan teks pesan (dari balasan atau argumen perintah)
teks_untuk_diproses = arg_handler.getMessage(message, is_arg=True)
print(f"Teks yang akan diproses: {teks_untuk_diproses}")

# Dapatkan string mention pengguna
# me = await client.get_me()
# mention = arg_handler.getMention(me) # <a href='tg://user?id=12345'>Nama Depan Belakang</a>
# print(mention)

# Dapatkan ID Pengguna dan alasan dari perintah seperti /ban <user> <alasan>
# user_id, reason = await arg_handler.getReasonAndId(message)
# print(f"ID Pengguna: {user_id}, Alasan: {reason}")
```

## Button

Membuat keyboard Pyrogram dengan mudah menggunakan sintaks berbasis teks yang sederhana.

- **Tombol Inline**: `| Teks Tombol - callback_data_atau_url |`
- **Tombol Reply**: `| Teks Tombol |`

```python
from nsdev import Button
# Asumsikan 'client' dan 'chat_id' sudah tersedia

button_handler = Button()

# --- Keyboard Inline ---
inline_text = """
Ini adalah pesan dengan tombol inline.
| Google - https://google.com | | GitHub - https://github.com |
| Peringatan - show_alert;same | | Profil - view_profile |
"""

# Keyword 'same' menempatkan tombol di baris yang sama dengan tombol sebelumnya.
inline_keyboard, teks_bersih = button_handler.create_keyboard(inline_text, inline_cmd="menu")
# await client.send_message(chat_id, teks_bersih, reply_markup=inline_keyboard)
print(teks_bersih)
print(inline_keyboard)


# --- Keyboard Reply ---
reply_text = """
Pilih salah satu opsi:
| Opsi 1 | | Opsi 2;same |
| Bantuan |
"""
reply_keyboard, teks_bersih2 = button_handler.create_reply_keyboard(reply_text)
# await client.send_message(chat_id, teks_bersih2, reply_markup=reply_keyboard)
print(teks_bersih2)
print(reply_keyboard)

# --- Hapus Keyboard Reply ---
# remove_markup = button_handler.remove_reply_keyboard()
# await client.send_message(chat_id, "Keyboard telah dihapus.", reply_markup=remove_markup)
```

## CipherHandler & AsciiManager

Enkripsi dan dekripsi string menggunakan berbagai metode. `CipherHandler` adalah implementasi yang lebih modern dan fleksibel.

```python
from nsdev import CipherHandler

# Inisialisasi dengan kunci dan metode ('bytes', 'shift', atau 'binary')
cipher = CipherHandler(key=123456789, method="bytes")

teks_asli = "Ini adalah pesan rahasia."

# Enkripsi
terenkripsi = cipher.encrypt(teks_asli)
print(f"Terenkripsi: {terenkripsi}")

# Dekripsi
terdekripsi = cipher.decrypt(terenkripsi)
print(f"Terdekripsi: {terdekripsi}")

# Anda juga bisa menyimpan kode terenkripsi ke file yang akan otomatis mendekripsi saat dieksekusi
# cipher.save("skrip_rahasia.py", "print('Halo dari file terenkripsi!')")
```

## DataBase

Wrapper database yang kuat dengan enkripsi bawaan yang mendukung file JSON lokal, SQLite, dan MongoDB.

```python
from nsdev import DataBase

# --- Inisialisasi ---

# Opsi 1: File JSON lokal (default)
db = DataBase(file_name="data_aplikasiku", auto_backup=False) # auto_backup memerlukan git

# Opsi 2: SQLite
# db = DataBase(storage_type="sqlite", file_name="db_aplikasiku")

# Opsi 3: MongoDB
# MONGO_URL = "mongodb://..."
# db = DataBase(storage_type="mongo", mongo_url=MONGO_URL, file_name="mongo_aplikasiku")

# --- Penggunaan ---
user_id = 12345

# Atur dan Ambil variabel
db.setVars(user_id, "username", "NorSodikin")
username = db.getVars(user_id, "username")
print(f"Username: {username}") # Output: NorSodikin

# Bekerja dengan list
db.setListVars(user_id, "roles", "admin")
db.setListVars(user_id, "roles", "moderator")
roles = db.getListVars(user_id, "roles")
print(f"Roles: {roles}") # Output: ['admin', 'moderator']

# Atur tanggal kedaluwarsa (misalnya, untuk akses pengguna)
db.setExp(user_id, exp=30) # Pengguna kedaluwarsa dalam 30 hari
sisa_hari = db.daysLeft(user_id)
print(f"Sisa hari: {sisa_hari}")

# Simpan data sesi bot
db.saveBot(user_id, "api_id_val", "api_hash_val", "session_string_val")
semua_bot = db.getBots()
print(f"Bot tersimpan: {len(semua_bot)}")

# Membersihkan data
db.removeAllVars(user_id)
db.removeBot(user_id)
db.close()
```

## Chatbot Gemini

Berintegrasi dengan model bahasa besar Gemini dari Google.

```python
from nsdev import ChatbotGemini

# Dapatkan API key Anda dari Google AI Studio
API_KEY = "API_KEY_GEMINI_ANDA"
bot = ChatbotGemini(api_key=API_KEY)

# --- Chat Umum ---
user_id = "user_123"
pesan_pengguna = "Hai, apa kabar? Ceritain lelucon dong!"
jawaban = bot.send_chat_message(pesan_pengguna, user_id, bot_name="AsistenAI")
print(jawaban)

# --- Cek Khodam (Mode Khusus) ---
# Mode ini menggunakan system prompt khusus untuk menghasilkan deskripsi "khodam".
nama = "Norsodikin"
deskripsi_khodam = bot.send_khodam_message(nama)
print(f"Khodam untuk {nama}: {deskripsi_khodam}")
```

## Gradient

Buat teks gradien yang indah dan bar kemajuan animasi di terminal Anda.

```python
import asyncio
from nsdev import Gradient

gradient = Gradient()

# --- Render teks gradien statis ---
gradient.render_text("NSDEV")

# --- Jalankan timer hitung mundur async ---
async def main():
    print("Memulai hitung mundur...")
    await gradient.countdown(10, text="Mohon tunggu selama {time}")
    print("\nSelesai!")
    
    ping_ms = await gradient.ping()
    print(f"Ping: {ping_ms:.2f} md")

# asyncio.run(main())
```

## ImageGenerator (Bing)

Hasilkan gambar AI menggunakan Bing Image Creator (endpoint DALL-E 3).

> **Catatan**: Modul ini memerlukan cookie otentikasi dari browser Anda. Masuk ke [bing.com/create](https://bing.com/create), buka alat pengembang (F12), buka tab Application/Storage, cari Cookies, dan salin nilai untuk `_U` dan `SRCHHPGUSR`.

```python
import asyncio
from nsdev import ImageGenerator

# Ini adalah contoh cookie, ganti dengan milik Anda
auth_cookie_u = "COOKIE_U_ANDA"
auth_cookie_srchhpgusr = "COOKIE_SRCHHPGUSR_ANDA"

image_gen = ImageGenerator(
    auth_cookie_u=auth_cookie_u,
    auth_cookie_srchhpgusr=auth_cookie_srchhpgusr
)

async def buat_gambar():
    prompt = "Seekor kucing lucu memakai topi penyihir, seni digital"
    try:
        url_gambar = await image_gen.generate(prompt, num_images=2)
        print("Gambar yang Dihasilkan:")
        for url in url_gambar:
            print(url)
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

# asyncio.run(buat_gambar())
```

## KeyManager

Utilitas untuk menyimpan dan mengambil kunci secara aman dari file sementara, berguna untuk mendistribusikan skrip tanpa menulis kredensial secara langsung.

Skrip akan memeriksa argumen baris perintah terlebih dahulu. Jika tidak ditemukan, skrip akan meminta pengguna untuk memasukkan kunci.

```bash
# Jalankan pertama kali (atau untuk mengatur kunci baru)
python skrip_anda.py --key 12345 --env .env.production
```

```python
# Di dalam skrip_anda.py
from nsdev import KeyManager

manager = KeyManager()

# Ini akan membaca dari argumen atau meminta input pengguna, lalu menyimpannya ke file sementara.
# Pada eksekusi berikutnya, ia akan membaca langsung dari file sementara.
key, nama_env = manager.handle_arguments()

print(f"Berhasil memuat Kunci: {key}")
print(f"File environment: {nama_env}")
```

## LoggerHandler

Logger yang sudah dikonfigurasi sebelumnya yang menyediakan output berwarna, terformat, dan disertai stempel waktu.

```python
from nsdev import LoggerHandler

# Inisialisasi logger
log = LoggerHandler()

log.info("Ini adalah pesan informasional.")
log.warning("Sepertinya ada yang salah.")
log.error("Terjadi kesalahan fatal!")

# Cetak sederhana dengan stempel waktu
log.print("Skrip telah dimulai dengan sukses.")
```

## Gateway Pembayaran

Integrasi dengan gateway pembayaran populer di Indonesia.

### PaymentMidtrans

```python
from nsdev import PaymentMidtrans

midtrans = PaymentMidtrans(
    server_key="SERVER_KEY_ANDA",
    client_key="CLIENT_KEY_ANDA",
    is_production=False
)

# Buat transaksi pembayaran
transaksi = midtrans.createPayment(order_id="order-123", gross_amount=50000)
url_pembayaran = transaksi['redirect_url']
print(f"Bayar di sini: {url_pembayaran}")

# Cek status transaksi
status = midtrans.checkTansactionStatus(order_id="order-123")
print(f"Status: {status['transaction_status']}")
```

### PaymentTripay

```python
from nsdev import PaymentTripay

tripay = PaymentTripay(api_key="API_KEY_TRIPAY_ANDA")

# Buat pembayaran
pembayaran = tripay.createPayment(
    method="QRIS",
    amount=10000,
    order_id="order-abc",
    customer_name="Budi Santoso"
)
print(f"Referensi pembayaran: {pembayaran.data.reference}")
print(f"URL Kode QR: {pembayaran.data.qr_url}")

# Cek status pembayaran
status = tripay.checkPayment(reference=pembayaran.data.reference)
print(f"Status: {status.data.status}")
```

### VioletMediaPayClient

```python
import asyncio
from nsdev import VioletMediaPayClient

violet = VioletMediaPayClient(
    api_key="API_KEY_ANDA",
    secret_key="SECRET_KEY_ANDA",
    live=False
)

async def main():
    # Buat pembayaran
    data_pembayaran = await violet.create_payment(amount="15000", produk="Akses Premium")
    ref_kode = data_pembayaran.ref_kode
    qr_code = data_pembayaran.api_response["qr_code"]
    print(f"Pindai kode QR ini: {qr_code}")

    # Cek status transaksi
    # Dalam skenario nyata, Anda akan mendapatkan ref_id dari callback
    # status = await violet.check_transaction(ref=ref_kode, ref_id="some_ref_id")
    # print(f"Status Transaksi: {status}")

# asyncio.run(main())
```

## Manajer Pengguna SSH

Menambah atau menghapus pengguna SSH dari jarak jauh di mesin Linux dan mendapatkan detail login melalui notifikasi bot Telegram.

> **Peringatan**: Modul ini memerlukan hak akses `sudo` untuk menjalankan perintah seperti `adduser` dan `deluser` di mesin host. Pastikan skrip dijalankan oleh pengguna dengan izin yang sesuai.

```python
from nsdev import SSHUserManager

# Inisialisasi dengan token bot Telegram dan ID obrolan Anda
manager = SSHUserManager(
    bot_token="7419614345:AAFwmSvM0zWNaLQhDLidtZ-B9Tzp-aVWICA",
    chat_id=1964437366
)

# Tambah pengguna baru dengan nama pengguna dan kata sandi acak
# Kredensial login akan dikirim ke obrolan Telegram Anda.
print("Menambahkan pengguna baru...")
manager.add_user()

# Tambah pengguna dengan nama pengguna dan kata sandi spesifik
# manager.add_user(ssh_username="penggunates", ssh_password="KataSandiAman123")

# Hapus pengguna
# print("Menghapus pengguna...")
# manager.delete_user("penggunates")
```

## YamlHandler

Memuat file `.yml` dan mengubahnya menjadi objek Python yang mudah diakses (`SimpleNamespace`), sehingga Anda dapat menggunakan notasi titik (`.`) alih-alih kunci kamus (`['']`).

**`config.yml`:**
```yaml
app:
  name: "Aplikasi Kerens"
  version: "1.0.2"
  debug_mode: true

database:
  host: "localhost"
  port: 5432
  users:
    - admin
    - guest
```

**`main.py`:**
```python
from nsdev import YamlHandler

yaml_handler = YamlHandler()
config = yaml_handler.loadAndConvert("config.yml")

if config:
    print(f"Nama Aplikasi: {config.app.name}")
    print(f"Mode Debug: {config.app.debug_mode}")
    print(f"Host DB: {config.database.host}")
    print(f"Pengguna DB Pertama: {config.database.users[0]}")
```
