# Pustaka Python `norsodikin`

[![Versi PyPI](https://img.shields.io/pypi/v/norsodikin.svg)](https://pypi.org/project/norsodikin/)
[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan toolkit sakti buat kamu yang mau bikin bot Telegram super canggih, ngelola server, enkripsi data, sampai mainan AI, semuanya jadi lebih gampang dan seru.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas bisa kamu akses langsung lewat `client.ns`, bikin kode bot-mu jadi lebih bersih, rapi, dan intuitif.

## Instalasi

Install `norsodikin` dan `pyrogram` itu gampang banget. Cukup jalankan perintah ini di terminal kamu:

```bash
pip install norsodikin pyrogram
```

Kalau kamu install dari *source code*, jangan lupa install semua dependensi dari file `requirements.txt` juga ya.

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

Mari kita bedah satu per satu semua modul keren yang ada di `client.ns`, diurutkan berdasarkan nama filenya.

---

### 1. `addUser` -> `client.ns.server.user`

Sangat praktis untuk mengelola user di server Linux. Kamu bisa nambah & hapus user SSH, lalu kirim detail loginnya langsung ke Telegram.

**Cara Pakai:**

```python
# Inisialisasi dengan token bot & chat ID tujuan kamu
manager = client.ns.server.user(bot_token="TOKEN_BOT_ANDA", chat_id=ID_CHAT_ANDA)

# --- Nambah user baru (username & pass acak) ---
print("Nambahin user baru...")
manager.add_user()
# Info login akan otomatis dikirim ke Telegram

# --- Nambah user baru (username & pass custom) ---
print("Nambahin user 'budi'...")
manager.add_user(ssh_username="budi", ssh_password="passwordkuat123")

# --- Hapus user ---
print("Ngapus user 'budi'...")
manager.delete_user(ssh_username="budi")
```
**Penting:** Skrip ini butuh hak akses `sudo` untuk menjalankan perintah `adduser` dan `deluser`.

---

### 2. `argument` -> `client.ns.telegram.arg`

Kumpulan fungsi praktis untuk membedah pesan, ngambil info user, dan cek status admin. Semua jadi lebih singkat dan jelas.

**Cara Pakai (di dalam handler Pyrogram):**

```python
# Misal pesan masuk: /kick @username soalnya bandel
# Atau balas pesan orang dengan: /kick

# Ambil user ID dan alasan dari pesan
user_id, reason = await client.ns.telegram.arg.getReasonAndId(message)
print(f"User ID: {user_id}, Alasan: {reason}")

# Ambil semua teks setelah command
query = client.ns.telegram.arg.getMessage(message, is_arg=True)
print(f"Query: {query}")
```

---

### 3. `bing` -> `client.ns.ai.bing`

Ubah imajinasimu jadi gambar keren pake Bing Image Creator. Kamu cuma butuh *cookie* otentikasi dari akun Bing-mu.

**Cara Pakai:**

```python
import asyncio

# Login dulu ke bing.com/create di browser, lalu copy-paste cookie di bawah.
BING_AUTH_COOKIE_U = "COOKIE_U_KAMU"
BING_AUTH_COOKIE_SRCHHPGUSR = "COOKIE_SRCHHPGUSR_KAMU"

bing_gen = client.ns.ai.bing(
    auth_cookie_u=BING_AUTH_COOKIE_U,
    auth_cookie_srchhpgusr=BING_AUTH_COOKIE_SRCHHPGUSR
)
    
prompt = "kucing astronot minum kopi di bulan"
list_url_gambar = await bing_gen.generate(prompt=prompt, num_images=4)
print(f"URL Gambar berhasil dibuat: {list_url_gambar}")
```

---

### 4. `button` -> `client.ns.telegram.button`

Lupakan pusingnya bikin keyboard Telegram. Dengan `client.ns.telegram.button`, kamu bisa bikin tombol inline atau reply pake sintaks berbasis teks yang gampang dibaca.

**Cara Pakai:**

```python
# --- 1. Keyboard Inline (Tombol di bawah pesan) ---
text_dengan_tombol = """
Pilih dong: | Tombol 1 - data1 | | Buka Google - https://google.com |
"""
inline_keyboard, sisa_teks = client.ns.telegram.button.create_inline_keyboard(text_dengan_tombol)
await message.reply(sisa_teks, reply_markup=inline_keyboard)

# --- 2. Keyboard Reply (Tombol di area ketik) ---
text_dengan_reply = "Halo! | Menu Utama - Kontak;same |"
reply_keyboard, sisa_teks_reply = client.ns.telegram.button.create_button_keyboard(text_dengan_reply)
await message.reply(sisa_teks_reply, reply_markup=reply_keyboard)
```

---

### 5. `colorize` -> `client.ns.utils.color`

Berikan sentuhan warna-warni ke output terminal skrip kamu agar tidak membosankan.

**Cara Pakai:**
```python
colors = client.ns.utils.color
print(f"{colors.GREEN}Pesan ini ijo!{colors.RESET}")
print(f"{colors.RED}Peringatan: Bahaya!{colors.RESET}")
```

---

### 6. `database` -> `client.ns.data.db`

Butuh tempat nyimpen data user? `client.ns.data.db` adalah solusinya! Fleksibel, mendukung penyimpanan JSON lokal, SQLite, hingga MongoDB, dan sudah dilengkapi enkripsi otomatis.

**Cara Pakai (Pake file JSON, paling simpel):**

```python
# Inisialisasi database (otomatis bikin file 'data_bot.json')
db = client.ns.data.db(storage_type="local", file_name="data_bot")

# Simpan dan ambil data buat user tertentu
user_id = 12345
db.setVars(user_id, "NAMA", "Budi")
nama = db.getVars(user_id, "NAMA") # -> "Budi"

# Set masa aktif dan cek sisanya
db.setExp(user_id, exp=30)
print(f"Masa aktif sisa: {db.daysLeft(user_id)} hari")
```

---

### 7. `encrypt` -> `client.ns.code`

Butuh cara cepet buat nyembunyiin atau nyamarkan data? `client.ns.code` nyediain beberapa metode enkripsi, masing-masing dengan keunikannya.

#### **Contoh dengan `CipherHandler` (Hasil berupa teks)**
Cocok untuk enkripsi umum yang hasilnya berupa string heksadesimal.
```python
# Akses kelas CipherHandler lewat namespace `code`
cipher = client.ns.code.Cipher(method="bytes", key="kunci_rahasia_123")
pesan_rahasia = "Ini adalah pesan yang sangat rahasia."

# Enkripsi pesannya
teks_terenkripsi = cipher.encrypt(pesan_rahasia)
print(f"Teks Terenkripsi: {teks_terenkripsi}") # Hasilnya string hex

# Dekripsi lagi
teks_asli = cipher.decrypt(teks_terenkripsi)
print(f"Teks Asli: {teks_asli}")
```

#### **Contoh dengan `AsciiManager` (Hasil berupa list angka)**
Metode ini mengubah teks menjadi list angka integer berdasarkan pergeseran ASCII, cocok untuk kasus tertentu di mana output list lebih berguna.
```python
# Akses kelas AsciiManager lewat namespace `code`
ascii_cipher = client.ns.code.Ascii(key="kunci_lain_bebas")
pesan_rahasia = "Pesan ini akan jadi angka."

# Enkripsi jadi list angka
list_angka_enkripsi = ascii_cipher.encrypt(pesan_rahasia)
print(f"List Angka Terenkripsi: {list_angka_enkripsi}") # Hasilnya [123, 456, ...]

# Dekripsi lagi dari list angka
teks_asli_ascii = ascii_cipher.decrypt(list_angka_enkripsi)
print(f"Teks Asli: {teks_asli_ascii}")
```

---

### 8. `gemini` -> `client.ns.ai.gemini`

Integrasikan AI canggih dari Google ke bot kamu. Bisa buat chatbot santai atau hiburan "cek khodam" yang lagi viral.

**Cara Pakai:**
```python
# Dapetin API Key kamu dari Google AI Studio
GEMINI_API_KEY = "API_KEY_KAMU"
chatbot = client.ns.ai.gemini(api_key=GEMINI_API_KEY)
user_id = 12345 # ID unik buat tiap user

# --- Mode Chatbot Santai ---
pertanyaan = "kasih aku jokes bapak-bapak dong"
jawaban = chatbot.send_chat_message(pertanyaan, user_id=user_id, bot_name="BotKeren")
print(f"Jawaban Bot: {jawaban}")
```

---

### 9. `gradient` -> `client.ns.utils.grad`

Hidupkan tampilan terminal dengan banner teks bergradien dan *countdown timer* animatif.

**Cara Pakai:**
```python
import asyncio

# Tampilkan banner dengan efek gradien
client.ns.utils.grad.render_text("Nor Sodikin")

# Bikin timer countdown dengan animasi
await client.ns.utils.grad.countdown(10, text="Tunggu {time} lagi...")
```

---

### 10. `listen` -> `client.listen()` & `chat.ask()`

Fitur spesial ini 'memperkuat' Pyrogram dengan menambahkan metode `.listen()` dan `.ask()` untuk membuat alur percakapan jadi sangat mudah. Untuk mengaktifkannya, Anda cukup mengimpor modul `listen` dari `nsdev` di awal skrip Anda. Proses *patching* akan terjadi secara otomatis.

**Cara Pakai:**
```python
import asyncio 
from pyrogram import Client, filters

# Cukup impor 'listen' untuk mengaktifkan .ask() dan .listen() pada Client
from nsdev import listen 

# Inisialisasi client Pyrogram Anda
app = Client("my_account")

@app.on_message(filters.command("tanya_nama") & filters.private)
async def tanya_nama(client, message):
    try:
        # Gunakan message.chat.ask() untuk mengirim pertanyaan dan menunggu jawaban
        jawaban = await message.chat.ask(
            "Hai! Siapa namamu?", 
            timeout=30
        )
        
        # 'jawaban' adalah objek Message dari balasan user
        await message.reply(f"Oh, halo {jawaban.text}! Senang bertemu denganmu.")

    except asyncio.TimeoutError:
        await message.reply("Waduh, kelamaan. Waktu habis!")
    except listen.UserCancelled: # Jika ada perintah lain yang membatalkan percakapan
        await message.reply("Oke, percakapan dibatalkan.")

print("Bot sedang berjalan...")
app.run()
```

---

### 11. `logger` -> `client.ns.utils.log`

Logger canggih pengganti `print()` yang mencatat pesan ke konsol dengan format rapi, penuh warna, lengkap dengan info waktu, file, dan fungsi.

**Cara Pakai:**
```python
def fungsi_penting():
    client.ns.utils.log.info("Memulai proses.")
    try:
        a = 10 / 0
    except Exception as e:
        client.ns.utils.log.error(f"Waduh, ada error: {e}")
```

---

### 12. `payment` -> `client.ns.payment`

Mau jualan di bot? Modul ini menyediakan klien untuk payment gateway populer. Cukup panggil kelas yang sesuai dari `client.ns.payment`.

#### **Contoh dengan `VioletMediaPay`**
```python
# live=False artinya pake mode testing/sandbox
violet_pay = client.ns.payment.Violet(
    api_key="API_KEY_VIOLET_KAMU", secret_key="SECRET_KEY_VIOLET_KAMU", live=False
)
payment = await violet_pay.create_payment(channel_payment="QRIS", amount="5000")
if payment.status:
    print(f"Link QR Code: {payment.data.target}")
```

#### **Contoh dengan `Midtrans`**
```python
midtrans_pay = client.ns.payment.Midtrans(
    server_key="SERVER_KEY_MIDTRANS", client_key="CLIENT_KEY_MIDTRANS", is_production=False
)
payment_info = midtrans_pay.create_payment(order_id="order-123", gross_amount=10000)
print(f"Link Pembayaran: {payment_info['redirect_url']}")
```

#### **Contoh dengan `Tripay`**
```python
tripay = client.ns.payment.Tripay(api_key="API_KEY_TRIPAY")
payment = tripay.create_payment(
    method="QRIS", amount=15000, order_id="trx-456", customer_name="Budi"
)
if payment.success:
    print(f"Kode Pembayaran: {payment.data.pay_code}")
    print(f"Link Checkout: {payment.data.checkout_url}")
```

---

### 13. `storekey` -> `client.ns.data.key`

`client.ns.data.key` ini kayak "brankas kecil" buat nyimpen data sensitif (misal kunci API) secara terenkripsi di file sementara, agar tidak *hardcode* di skrip.

**Cara Pakai (di awal skrip kamu):**

```python
# Inisialisasi KeyManager
key_manager = client.ns.data.key(filename="kunci_rahasia_app.json")

# Panggil fungsi ini di awal. Jika file belum ada, akan minta input.
kunci, nama_env = key_manager.handle_arguments()
print(f"Kunci yang dipakai: {kunci}")
```

---

### 14. `ymlreder` -> `client.ns.data.yaml`

Mengubah file konfigurasi `.yml` menjadi objek Python yang bisa diakses pake notasi titik. Sangat praktis!

**Cara Pakai:**

Misal punya `config.yml`: `{ database: { host: localhost, port: 5432 }}`

```python
config = client.ns.data.yaml.loadAndConvert("config.yml")
if config:
    # Akses datanya jadi gampang!
    print(f"Host: {config.database.host}")
```

## Penggunaan Standalone (Tanpa Pyrogram)

Meskipun dirancang untuk Pyrogram, kamu tetap bisa pake modul-modul ini secara terpisah di proyek Python lain.

```python
from nsdev import DataBase, AnsiColors, ChatbotGemini
# ...dan seterusnya
```

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, kamu bebas pakai, modifikasi, dan distribusikan untuk proyek apa pun.

---

Semoga dokumentasi ini bikin kamu makin semangat ngoding! Selamat mencoba dan berkreasi dengan `norsodikin`. Jika ada pertanyaan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
