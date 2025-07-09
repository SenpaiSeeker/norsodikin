# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`, sebuah koleksi module Python serbaguna yang kini **terintegrasi penuh dengan Pyrogram**. Pustaka ini dirancang untuk memperluas kemampuan bot Telegram Anda dengan cara yang intuitif dan bersih, mulai dari manajemen server, enkripsi data, hingga interaksi dengan berbagai API canggih.

## Fitur Utama
*   **Integrasi Mulus**: Tidak perlu impor manual yang berantakan. Cukup impor `nsdev` sekali, dan semua fungsionalitas akan "menempel" pada objek `client` Pyrogram Anda.
*   **Kode Bersih**: Akses semua modul melalui `client.ns`, membuat alur kerja Anda lebih terstruktur dan mudah dibaca.
*   **Serbaguna**: Dilengkapi dengan berbagai alat, mulai dari pembuat tombol, interaksi AI (Gemini, Bing Image), manajemen database, hingga integrasi payment gateway.

## Instalasi

Untuk menginstal pustaka ini, cukup jalankan perintah berikut di terminal Anda:

```bash
pip install norsodikin -U
```

Pastikan Anda juga telah menginstal `pyrogram` dan dependensi lainnya. Pustaka ini akan menangani sebagian besar dependensi secara otomatis.

## Cara Penggunaan Baru (Integrasi Otomatis)

Pustaka `norsodikin` versi baru menggunakan teknik *monkey-patching* untuk menyuntikkan semua fungsionalitasnya langsung ke dalam Pyrogram. Cukup `import nsdev` di awal skrip Anda, dan semua `client` Pyrogram yang dibuat setelahnya akan otomatis memiliki *accessor* `.ns`.

```python
import nsdev  # <-- Cukup impor ini sekali di bagian atas!
from pyrogram import Client, filters
from pyrogram.types import Message

# Inisialisasi client seperti biasa
app = Client("my_bot", api_id=..., api_hash=..., bot_token=...)

# Sekarang, semua fungsionalitas norsodikin tersedia di `app.ns`
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    # Contoh penggunaan logger
    client.ns.logger.info(f"User {message.from_user.id} memulai bot.")
    
    # Contoh penggunaan argument
    user_mention = client.ns.argument.getMention(message.from_user)
    
    await message.reply_text(f"Halo, {user_mention}!")

# Jalankan bot
app.run()
```
Struktur ini menghilangkan kebutuhan untuk menginisialisasi setiap kelas modul secara manual.

---

## Panduan Lengkap Module (`client.ns`)

Berikut adalah panduan lengkap untuk setiap module yang tersedia di dalam `client.ns`.

### 1. `ns.addUser` - Manajemen Pengguna SSH
Mengelola pengguna di server Linux dan mengirim detailnya ke Telegram.

**Cara Penggunaan:**
```python
# Asumsikan handler ini dipicu oleh admin di chat tertentu
# /addssh atau /delssh budi
@app.on_message(filters.command("addssh") & filters.private)
async def add_ssh_user(client: Client, message: Message):
    await message.reply("Memproses permintaan untuk menambah pengguna SSH baru...")
    # Mengirim detail ke chat ID pengirim pesan
    await client.ns.addUser.add_user(chat_id=message.chat.id)
    # Anda juga bisa mengirim ke channel/grup spesifik
    # await client.ns.addUser.add_user(chat_id=-10012345678)

@app.on_message(filters.command("delssh") & filters.private)
async def del_ssh_user(client: Client, message: Message):
    try:
        username = message.command[1]
        await message.reply(f"Memproses penghapusan pengguna '{username}'...")
        await client.ns.addUser.delete_user(
            chat_id=message.chat.id, 
            ssh_username=username
        )
    except IndexError:
        await message.reply("Gunakan: /delssh <username>")
```
**Catatan:** Skrip ini memerlukan hak akses `sudo` untuk `adduser` dan `deluser`.

---

### 2. `ns.argument` - Asisten Argument Pyrogram
Kumpulan fungsi praktis untuk mem-parsing pesan, mendapatkan info pengguna, dan memeriksa status admin.

**Cara Penggunaan:**
```python
# Misal pesan: /kick @username alasannya
@app.on_message(filters.command("kick"))
async def kick_handler(client: Client, message: Message):
    # Mendapatkan user ID dan alasan
    user_id, reason = await client.ns.argument.getReasonAndId(message)
    print(f"User ID to kick: {user_id}, Reason: {reason}")
    
    # Cek apakah pengirim pesan adalah admin
    is_admin = await client.ns.argument.getAdmin(message)
    print(f"Is sender an admin? {is_admin}")

    # Mendapatkan teks argumen saja
    query = client.ns.argument.getMessage(message, is_arg=True)
    print(f"Full argument string: {query}")
    
    # Membuat mention HTML
    me = await client.get_me()
    my_mention = client.ns.argument.getMention(me) # -> <a href='...'>Nama Bot</a>
    print(f"Bot mention: {my_mention}")
```

---

### 3. `ns.bing` - Pembuat Gambar AI (Bing)
Menghasilkan gambar dari teks menggunakan Bing Image Creator. Module ini adalah sebuah *class*, jadi Anda perlu menginisialisasinya.

**Cara Penggunaan:**
```python
# /imagine seekor rubah cyberpunk
@app.on_message(filters.command("imagine"))
async def imagine_handler(client: Client, message: Message):
    prompt = client.ns.argument.getMessage(message, is_arg=True)
    if not prompt:
        return await message.reply("Berikan prompt gambar!")
        
    msg = await message.reply("Sedang melukis imajinasimu... 🎨")

    try:
        # Inisialisasi generator dari client.ns.bing
        bing_gen = client.ns.bing(
            auth_cookie_u="COOKIE_U_ANDA",
            auth_cookie_srchhpgusr="COOKIE_SRCHHPGUSR_ANDA"
        )
        image_urls = await bing_gen.generate(prompt=prompt, num_images=1)
        
        if image_urls:
            await client.send_photo(message.chat.id, image_urls[0], caption=f"✨ **Prompt**: `{prompt}`")
            await msg.delete()
        else:
            await msg.edit("Gagal membuat gambar, mungkin prompt tidak aman.")
            
    except Exception as e:
        await msg.edit(f"Terjadi kesalahan: {e}")
```

---

### 4. `ns.button` - Pembuat Tombol Keren untuk Telegram
Menyederhanakan pembuatan tombol *inline* atau *reply* dengan syntax berbasis teks.

**Cara Penggunaan:**
```python
@app.on_message(filters.command("menu"))
async def menu_handler(client: Client, message: Message):
    text_with_buttons = """
    Selamat datang! Silakan pilih menu di bawah.
    | Tombol Inline 1 - data1 |
    | Google - https://google.com | | Bantuan - help_cb;same |
    """
    
    # Membuat keyboard inline
    inline_keyboard, remaining_text = client.ns.button.create_keyboard(text_with_buttons)
    await message.reply(remaining_text, reply_markup=inline_keyboard)

    # Membuat keyboard reply
    text_reply = """
    Pilih Opsi:
    | Menu Utama - Kontak;same |
    """
    reply_keyboard, text_reply_only = client.ns.button.create_reply_keyboard(text_reply)
    await message.reply(text_reply_only, reply_markup=reply_keyboard)
```

---

### 5. `ns.colorize` - Pewarna Teks Terminal
Memberikan warna pada output di konsol/terminal.

**Cara Penggunaan:**
```python
# Kode ini dijalankan di terminal, bukan di bot
def my_local_script():
    # Akses objek colorize yang sudah ada
    colors = nsdev.Client("dummy").ns.colorize # Atau bisa impor langsung AnsiColors
    
    print(f"{colors.GREEN}Pesan ini berwarna hijau!{colors.RESET}")
    print(f"{colors.RED}Peringatan: Ada kesalahan!{colors.RESET}")
    
    # Cetak semua warna
    colors.print_all_colors()
```
*Catatan: Untuk penggunaan di luar handler Pyrogram, Anda bisa mengimpor kelas `AnsiColors` secara langsung atau membuat instance dummy seperti di atas.*

---

### 6. `ns.database` - Database Serbaguna dengan Enkripsi
Solusi penyimpanan data fleksibel (JSON, MongoDB, SQLite) dengan enkripsi otomatis.

**Cara Penggunaan:**
```python
# Inisialisasi database di dalam handler
@app.on_message(filters.command("setdata"))
async def set_data_handler(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Inisialisasi Database (bisa diletakkan di luar handler jika dipakai berulang)
    db = client.ns.database(storage_type="local", file_name="my_bot_data")
    
    db.setVars(user_id, "NAMA", message.from_user.first_name)
    db.setListVars(user_id, "HOBI", "Coding")
    
    await message.reply("Data Anda telah disimpan!")
    db.close()

@app.on_message(filters.command("getdata"))
async def get_data_handler(client: Client, message: Message):
    user_id = message.from_user.id
    db = client.ns.database(storage_type="local", file_name="my_bot_data")
    
    nama = db.getVars(user_id, "NAMA")
    hobi = db.getListVars(user_id, "HOBI")
    
    await message.reply(f"Nama: {nama}\nHobi: {hobi}")
    db.close()
```

---

### 7. `ns.encrypt` - Enkripsi dan Dekripsi
Menyediakan beberapa metode enkripsi sederhana. Terdapat dua kelas utama: `CipherHandler` dan `AsciiManager`.

**Cara Penggunaan `CipherHandler`:**
```python
# Inisialisasi CipherHandler dari client.ns
# Pilihan method: 'bytes', 'binary', 'shift'
cipher = client.ns.encrypt(method="bytes", key=123456789)

pesan_rahasia = "Ini pesan yang sangat rahasia."
enkripsi = cipher.encrypt(pesan_rahasia)
dekripsi = cipher.decrypt(enkripsi)

print(f"Terenkripsi: {enkripsi}")
print(f"Terdekripsi: {dekripsi}")
```

**Cara Penggunaan `AsciiManager`:**
*Untuk menggunakan `AsciiManager`, Anda perlu mengimpornya secara terpisah.*
```python
from nsdev.encrypt import AsciiManager

ascii_cipher = AsciiManager(key=98765)
encrypted_list = ascii_cipher.encrypt("Hello World")
decrypted_string = ascii_cipher.decrypt(encrypted_list)

print(f"ASCII Terenkripsi: {encrypted_list}")
print(f"ASCII Terdekripsi: {decrypted_string}")
```

---

### 8. `ns.gemini` - Ngobrol dengan AI Google Gemini
Jembatan untuk berinteraksi dengan model AI Gemini dari Google.

**Cara Penggunaan:**
```python
GEMINI_API_KEY = "API_KEY_ANDA"

@app.on_message(filters.command("ai"))
async def ai_handler(client: Client, message: Message):
    pertanyaan = client.ns.argument.getMessage(message, is_arg=True)
    if not pertanyaan:
        return await message.reply("Tanya apa?")
        
    # Inisialisasi chatbot Gemini
    chatbot = client.ns.gemini(api_key=GEMINI_API_KEY)
    
    user_id = message.from_user.id # ID unik agar history chat tidak tercampur
    jawaban = chatbot.send_chat_message(pertanyaan, user_id=user_id, bot_name="BotKeren")
    await message.reply(jawaban)

@app.on_message(filters.command("khodam"))
async def khodam_handler(client: Client, message: Message):
    nama = client.ns.argument.getMessage(message, is_arg=True) or message.from_user.first_name
    chatbot = client.ns.gemini(api_key=GEMINI_API_KEY)
    
    await message.reply(f"Mengecek khodam untuk **{nama}**...")
    deskripsi_khodam = chatbot.send_khodam_message(nama)
    await message.reply(deskripsi_khodam)
```

---

### 9. `ns.gradient` - Efek Teks Keren di Terminal
Membuat banner teks gradien dan countdown timer animatif di terminal.

**Cara Penggunaan (di skrip lokal):**
```python
import asyncio
import nsdev

# Membuat instance gradient
gradient_effect = nsdev.Client("dummy").ns.gradient

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

### 10. `ns.logger` - Pencatat Log Informatif
Versi canggih dari `print()` yang mencatat pesan ke konsol dengan format rapi dan berwarna.

**Cara Penggunaan:**
```python
@app.on_message(filters.text & filters.private)
async def log_message(client: Client, message: Message):
    # Cukup panggil fungsi log dari client.ns.logger
    client.ns.logger.info(f"Menerima pesan dari {message.from_user.id}")
    try:
        # Some process that might fail
        x = 1 / 0
    except Exception as e:
        client.ns.logger.error(f"Terjadi kesalahan saat memproses pesan: {e}")
```

---

### 11. `ns.payment` - Integrasi Payment Gateway
Menyediakan klien untuk Midtrans, Tripay, dan VioletMediaPay.

**Cara Penggunaan (Contoh `VioletMediaPay`):**
```python
VIOLET_API_KEY = "API_KEY_ANDA"
VIOLET_SECRET_KEY = "SECRET_KEY_ANDA"

@app.on_message(filters.command("donate"))
async def donate_handler(client: Client, message: Message):
    # Inisialisasi klien (live=False untuk mode testing)
    payment_client = client.ns.payment_violet(
        api_key=VIOLET_API_KEY, 
        secret_key=VIOLET_SECRET_KEY, 
        live=False
    )
    
    msg = await message.reply("Membuat link donasi QRIS Rp 5.000...")
    
    try:
        payment = await payment_client.create_payment(
            channel_payment="QRIS",
            amount="5000",
            produk="Donasi Kopi"
        )
        if payment.api_response.success:
            qr_url = payment.api_response.data.qrcode_url
            expired = payment.api_response.data.expired_time_format
            await msg.edit(f"Silakan scan QR ini untuk donasi: {qr_url}\nBayar sebelum: {expired}")
        else:
            await msg.edit(f"Gagal membuat pembayaran: {payment.api_response.message}")
    except Exception as e:
        await msg.edit(f"Terjadi error: {e}")
```
*Untuk `payment_midtrans` dan `payment_tripay`, polanya sama: inisialisasi kelasnya dari `client.ns` lalu panggil metodenya.*

---

### 12. `ns.storekey` - Penyimpanan Kunci yang Aman
Brankas kecil untuk menyimpan data sensitif di file sementara yang terenkripsi.

**Cara Penggunaan:**
Fungsi ini biasanya dipanggil saat memulai skrip dari terminal.
```python
# Di dalam skrip Python kamu
import nsdev
from pyrogram import Client

# Panggil fungsi ini di awal skrip sebelum inisialisasi client
# Jika file kunci belum ada, pengguna akan diminta input.
# Akses melalui instance dummy atau sebelum loop bot
key_manager = nsdev.Client("dummy").ns.storekey
kunci, nama_env = key_manager.handle_arguments()

print(f"Kunci yang digunakan: {kunci}")
print(f"Nama Environment: {nama_env}")

# Lanjutkan dengan inisialisasi bot Anda...
# app = Client("my_bot", ...)
# app.run()
```
Anda juga bisa mengatur kuncinya dari command line: `python skrip_kamu.py --key 12345 --env .env_dev`

---

### 13. `ns.yaml_reader` - Pembaca File YAML Praktis
Mengubah file `.yml` menjadi objek Python yang mudah diakses.

**Cara Penggunaan:**
Asumsikan ada file `config.yml`:
```yml
database:
  host: "localhost"
  user: "admin"
api_keys:
  - name: "telegram"
    key: "abc-456"
```

Lalu di Python:
```python
@app.on_message(filters.command("config"))
async def config_handler(client: Client, message: Message):
    # Membaca dan mengubah file YAML menjadi objek
    config = client.ns.yaml_reader.loadAndConvert("config.yml")

    if config:
        db_host = config.database.host
        api_key_name = config.api_keys[0].name
        
        await message.reply(
            f"Host DB dari config: {db_host}\n"
            f"Nama API pertama: {api_key_name}"
        )
    else:
        await message.reply("File config.yml tidak ditemukan atau error.")
```

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Kamu bebas menggunakan, memodifikasi, dan mendistribusikannya.

---

Semoga dokumentasi ini membantumu! Selamat mencoba dan berkreasi dengan [norsodikin](https://t.me/NorSodikin).
