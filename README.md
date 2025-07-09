# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`, sebuah koleksi modul Python serbaguna yang dirancang untuk mempermudah berbagai tugas, mulai dari manajemen server, enkripsi data, hingga pembuatan bot Telegram yang canggih. Pustaka ini dirancang untuk berintegrasi secara mulus dengan **Pyrogram**.

## Instalasi

Untuk menginstal pustaka ini, cukup jalankan perintah berikut di terminal Anda:

```bash
pip install norsodikin
```

Pastikan juga semua dependensi dari file `requirements.txt` sudah terpasang jika Anda meng-install dari source.

## Integrasi dengan Pyrogram (Sangat Penting!)

`norsodikin` secara otomatis "menyuntikkan" dirinya ke dalam `pyrogram.Client`. Anda **tidak perlu melakukan inisialisasi tambahan**. Cukup impor `nsdev` atau Pyrogram seperti biasa, dan semua fungsionalitas akan tersedia melalui `client.ns`.

**Contoh Penggunaan Dasar:**
```python
from pyrogram import Client, filters
from pyrogram.types import Message

# Cukup impor 'nsdev' sekali di skrip Anda untuk mengaktifkan integrasi.
import nsdev 

# Buat client Pyrogram Anda seperti biasa.
# Semua fungsionalitas 'nsdev' akan otomatis tersedia di 'app.ns'
app = Client("my_account") 

@app.on_message(filters.command("myinfo"))
async def my_info_handler(client: Client, message: Message):
    # Gunakan modul 'argument' melalui client.ns
    mention = client.ns.argument.getMention(message.from_user, tag_and_id=True)
    await message.reply_text(f"Halo, ini info kamu: {mention}")

# Semua contoh di bawah ini mengasumsikan Anda sudah memiliki 
# objek 'client' atau 'app' yang aktif.
```

---

## Panduan Penggunaan Modul

Berikut adalah panduan lengkap untuk setiap modul yang tersedia di dalam `client.ns`.

---

### 1. `client.ns.addUser` - Manajemen Pengguna SSH

Modul ini sangat berguna untuk mengelola pengguna di server Linux. Dengan `client.ns.addUser`, Anda bisa menambah dan menghapus pengguna SSH secara otomatis dan mengirimkan detailnya langsung ke Telegram.

**Cara Penggunaan (dalam sebuah handler Pyrogram):**

```python
# /addssh -> Menambah user dengan username & password acak
@app.on_message(filters.command("addssh") & filters.private)
async def add_ssh_user(client: Client, message: Message):
    msg = await message.reply("Sedang memproses penambahan user SSH...")
    await client.ns.addUser.add_user(chat_id=message.chat.id)
    await msg.delete() # Pesan notifikasi akan dikirim terpisah

# /delssh budi -> Menghapus user 'budi'
@app.on_message(filters.command("delssh") & filters.private)
async def delete_ssh_user(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply("Gunakan: /delssh <username>")
        return
    username_to_delete = message.command[1]
    msg = await message.reply(f"Sedang menghapus user '{username_to_delete}'...")
    await client.ns.addUser.delete_user(
        chat_id=message.chat.id, 
        ssh_username=username_to_delete
    )
    await msg.delete()
```
**Catatan:** Skrip ini memerlukan hak akses `sudo` untuk menjalankan perintah `adduser` dan `deluser`.

---

### 2. `client.ns.argument` - Asisten Argument Pyrogram

Teman terbaik Anda untuk membangun bot dengan Pyrogram. Isinya kumpulan fungsi praktis untuk mem-parsing pesan, mendapatkan info pengguna, dan memeriksa status admin.

**Cara Penggunaan (dalam sebuah handler Pyrogram):**

```python
# Misal pesan yang diterima adalah: /kick @username alasannya
# Atau membalas pesan seseorang dengan: /kick alasannya
@app.on_message(filters.command("kick"))
async def kick_handler(client: Client, message: Message):
    # Mendapatkan user ID dan alasan dari sebuah pesan
    user_id, reason = await client.ns.argument.getReasonAndId(message)
    print(f"User ID: {user_id}, Alasan: {reason}")

    # Mendapatkan teks dari pesan (argument setelah command)
    query = client.ns.argument.getMessage(message, is_arg=True)
    print(f"Query: {query}")

    # Membuat tag mention HTML untuk pengguna
    me = await client.get_me()
    mention = client.ns.argument.getMention(me) # -> <a href='tg://user?id=...'>Nama Depan</a>
    print(f"Mention untuk bot: {mention}")

    # Cek apakah pengguna adalah admin
    is_admin = await client.ns.argument.getAdmin(message)
    print(f"Apakah user seorang admin? {is_admin}")
```

---

### 3. `client.ns.bing` - Pembuat Gambar AI (Bing)

Ingin membuat gambar dari teks menggunakan AI Bing? Anda hanya perlu memberikan *cookie* otentikasi.

**Cara Penggunaan:**

```python
import asyncio

# Anda harus login ke bing.com di browser, lalu salin nilai cookie _U dan SRCHHPGUSR.
BING_AUTH_COOKIE_U = "COOKIE_U_ANDA"
BING_AUTH_COOKIE_SRCHHPGUSR = "COOKIE_SRCHHPGUSR_ANDA"

@app.on_message(filters.command("createimg"))
async def generate_image(client: Client, message: Message):
    prompt = client.ns.argument.getMessage(message, is_arg=True)
    if not prompt:
        await message.reply("Gunakan: /createimg <deskripsi gambar>")
        return

    try:
        # Inisialisasi kelas generator melalui client.ns.bing
        bing_image_gen = client.ns.bing(
            auth_cookie_u=BING_AUTH_COOKIE_U,
            auth_cookie_srchhpgusr=BING_AUTH_COOKIE_SRCHHPGUSR
        )
        
        processing_msg = await message.reply(f"Membuat gambar dengan prompt: '{prompt}'...")
        image_urls = await bing_image_gen.generate(prompt=prompt, num_images=1)

        if image_urls:
            await client.send_photo(message.chat.id, image_urls[0], caption=f"Hasil untuk: `{prompt}`")
            await processing_msg.delete()
        else:
            await processing_msg.edit("Gagal membuat gambar.")
            
    except Exception as e:
        await message.reply(f"Terjadi kesalahan: {e}")
```

---

### 4. `client.ns.button` - Pembuat Tombol Keren untuk Telegram

Sederhanakan pembuatan tombol *inline* atau *reply* dengan syntax berbasis teks yang unik.

**Cara Penggunaan:**
```python
@app.on_message(filters.command("menu"))
async def show_menu(client: Client, message: Message):
    # Akses pembuat tombol melalui client.ns.button
    button_builder = client.ns.button

    # 1. Membuat Keyboard Inline
    text_with_buttons = """
    Ini adalah pesan dengan tombol inline. Pilih salah satu:
    | Tombol 1 - data1 |
    | Tombol 2 - data2 |
    | Google - https://google.com | | Bantuan - help;same |
    """
    
    inline_keyboard, remaining_text = button_builder.create_keyboard(text_with_buttons)

    await message.reply(
        text=remaining_text,
        reply_markup=inline_keyboard
    )
```

---

### 5. `client.ns.colorize` - Pewarna Teks Terminal

Beri sentuhan warna-warni pada output skrip Anda di konsol.

**Cara Penggunaan:**

```python
# Akses warna melalui client.ns.colorize
colors = app.ns.colorize

print(f"{colors.GREEN}Pesan ini berwarna hijau!{colors.RESET}")
print(f"{colors.RED}Peringatan: Ada kesalahan!{colors.RESET}")

# Cetak semua warna yang tersedia
colors.print_all_colors()
```

---

### 6. `client.ns.database` - Database Serbaguna dengan Enkripsi

Solusi penyimpanan fleksibel (JSON, MongoDB, SQLite) dengan enkripsi otomatis.

**Cara Penggunaan:**
```python
@app.on_message(filters.command("setdata"))
async def set_user_data(client: Client, message: Message):
    # Akses kelas DataBase melalui client.ns.database
    # Inisialisasi DB (bisa dibuat global jika sering diakses)
    db = client.ns.database(storage_type="local", file_name="my_bot_data")
    
    user_id = message.from_user.id
    db.setVars(user_id, "NAMA", message.from_user.first_name)
    db.setVars(user_id, "LEVEL", 10)
    
    nama = db.getVars(user_id, "NAMA")
    await message.reply(f"Data disimpan. Nama Anda di DB adalah: {nama}")
    
    db.close() # Penting jika tidak dipakai lagi
```

---

### 7. `client.ns.encrypt` - Enkripsi dan Dekripsi Sederhana

Butuh cara cepat untuk menyamarkan data? Gunakan `CipherHandler`.

**Cara Penggunaan:**
```python
# Inisialisasi kelas CipherHandler melalui client.ns.encrypt
cipher = app.ns.encrypt(method="bytes", key=123456789)

pesan_rahasia = "Ini adalah pesan yang sangat rahasia."
encrypted_text = cipher.encrypt(pesan_rahasia)
decrypted_text = cipher.decrypt(encrypted_text)

print(f"Terenkripsi: {encrypted_text}")
print(f"Terdekripsi: {decrypted_text}")
```

---

### 8. `client.ns.gemini` - Ngobrol dengan AI Google Gemini

Berinteraksi dengan model AI Gemini dari Google.

**Cara Penggunaan:**
```python
# Ganti dengan API Key Anda
GEMINI_API_KEY = "API_KEY_ANDA"

# Inisialisasi kelas ChatbotGemini melalui client.ns.gemini
chatbot = app.ns.gemini(api_key=GEMINI_API_KEY)

@app.on_message(filters.command("khodam") & filters.private)
async def cek_khodam(client: Client, message: Message):
    nama = message.from_user.full_name
    deskripsi_khodam = chatbot.send_khodam_message(nama)
    await message.reply(f"--- Hasil Cek Khodam untuk {nama} ---\n\n{deskripsi_khodam}")
```

---

### 9. `client.ns.gradient` - Efek Teks Keren di Terminal

Buat banner teks gradien dan *countdown timer* animatif di terminal Anda.

**Cara Penggunaan:**
```python
import asyncio

# Akses objek gradient melalui client.ns.gradient
gradient_effect = app.ns.gradient

# 1. Render teks dengan efek gradien
gradient_effect.render_text("Norsodikin")

# 2. Countdown timer animatif (jalankan dalam fungsi async)
async def run_countdown():
    print("\nMemulai hitung mundur...")
    await gradient_effect.countdown(10)

asyncio.run(run_countdown())
```

---

### 10. `client.ns.logger` - Pencatat Log Informatif

Gunakan `client.ns.logger` sebagai pengganti `print()` untuk logging yang rapi dan berwarna.

**Cara Penggunaan:**
```python
# Akses logger melalui client.ns.logger
log = app.ns.logger

def fungsi_penting():
    log.info("Memulai proses penting.")
    try:
        a = 10 / 0
    except Exception as e:
        log.error(f"Terjadi kesalahan: {e}")

fungsi_penting()
```

---

### 11. `client.ns.payment` - Integrasi Payment Gateway

Menyediakan klien untuk Midtrans (`payment_midtrans`), Tripay (`payment_tripay`), dan VioletMediaPay (`payment_violet`).

**Cara Penggunaan (Contoh dengan `VioletMediaPayClient`):**

```python
import asyncio

VIOLET_API_KEY = "API_KEY_ANDA"
VIOLET_SECRET_KEY = "SECRET_KEY_ANDA"

async def buat_pembayaran():
    # Inisialisasi klien melalui client.ns.payment_violet
    # (live=False untuk mode sandbox/testing)
    payment_client = app.ns.payment_violet(
        api_key=VIOLET_API_KEY, 
        secret_key=VIOLET_SECRET_KEY, 
        live=False
    )
    
    payment = await payment_client.create_payment(amount="5000", produk="Donasi Kopi")
    if payment.api_response.success:
        print(f"Link QR Code: {payment.api_response.data.qrcode_url}")
    else:
        print(f"Gagal: {payment.api_response.message}")

asyncio.run(buat_pembayaran())
```

---

### 12. `client.ns.storekey` - Penyimpanan Kunci yang Aman

Brankas kecil untuk menyimpan data sensitif di file sementara yang terenkripsi. Berguna saat menjalankan skrip dari terminal.

**Cara Penggunaan:**

```python
# Di dalam skrip Python yang dijalankan dari terminal
from pyrogram import Client
import nsdev # Aktifkan integrasi

app = Client("my_bot_setup")

# Akses key_manager dari client.ns.storekey
key_manager = app.ns.storekey

# Panggil fungsi ini di awal skrip
# Jika file kunci belum ada, pengguna akan diminta untuk memasukkannya.
kunci, nama_env = key_manager.handle_arguments()

print(f"Kunci yang digunakan: {kunci}")
print(f"Nama Environment: {nama_env}")
```
*Atur kunci via command line: `python skrip_kamu.py --key 12345 --env .env_dev`*

---

### 13. `client.ns.yaml_reader` - Pembaca File YAML Praktis

Mengubah file konfigurasi `.yml` menjadi objek Python yang mudah diakses.

**Cara Penggunaan:**

Anggap Anda punya file `config.yml`:
```yml
database:
  host: "localhost"
  user: "admin"
api_keys:
  - name: "google"
    key: "xyz-123"
```
Di Python:
```python
# Akses pembaca YAML melalui client.ns.yaml_reader
reader = app.ns.yaml_reader

config = reader.loadAndConvert("config.yml")

if config:
    # Akses data dengan notasi titik
    db_host = config.database.host
    api_name = config.api_keys[0].name
    print(f"Host Database: {db_host}")
    print(f"API pertama: {api_name}")
```

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Kamu bebas menggunakan, memodifikasi, dan mendistribusikannya.

---

Semoga dokumentasi ini membantumu! Selamat mencoba dan berkreasi dengan [norsodikin](https://t.me/NorSodikin).
