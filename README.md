# norsodikin

![version](https://img.shields.io/badge/version-0.7.1-blue)
![python](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-green)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

Pustaka `norsodikin` adalah kumpulan alat dan utilitas serbaguna yang dirancang untuk berbagai keperluan, mulai dari manajemen sistem, enkripsi data, integrasi API, hingga pembuatan antarmuka baris perintah yang menarik.

## Instalasi

Anda dapat menginstal pustaka ini menggunakan `pip`:

```bash
pip install norsodikin
```

Pustaka ini akan otomatis menginstal semua dependensi yang diperlukan.

## Panduan Penggunaan Modul

Berikut adalah penjelasan dan contoh penggunaan untuk setiap modul yang tersedia.

### 1. SSH User Manager (`addUser`)

Modul ini memudahkan manajemen pengguna SSH pada sistem Linux, seperti menambah dan menghapus pengguna, serta mengirimkan notifikasi kredensial melalui Telegram.

**Penting:** Penggunaan modul ini memerlukan hak akses `sudo`.

**Contoh Penggunaan:**

```python
from nsdev import SSHUserManager

# Inisialisasi dengan token bot Telegram dan chat ID Anda
# Nilai default akan digunakan jika tidak disediakan
manager = SSHUserManager(bot_token="YOUR_TELEGRAM_BOT_TOKEN", chat_id="YOUR_TELEGRAM_CHAT_ID")

# Menambah pengguna baru dengan nama dan kata sandi acak
manager.add_user()

# Menambah pengguna baru dengan nama dan kata sandi yang ditentukan
manager.add_user(ssh_username="user_test", ssh_password="password123")

# Menghapus pengguna
manager.delete_user(ssh_username="user_test")
```

### 2. Pyrogram Argument Helper (`argument`)

Kelas ini berisi fungsi-fungsi pembantu untuk mem-parsing argumen dari objek `message` di Pyrogram.

**Contoh Penggunaan:**

```python
from nsdev import Argument

# Asumsikan 'message' adalah objek pesan dari Pyrogram
# dan 'client' adalah objek klien Pyrogram.

arg_handler = Argument()

# Mengambil teks dari pesan (bisa dari balasan atau argumen)
# text = arg_handler.getMessage(message, is_arg=True)
# print(f"Teks yang didapat: {text}")

# Mendapatkan user ID dan alasan dari sebuah perintah (misal: /ban @user alasan)
# user_id, reason = await arg_handler.getReasonAndId(message)
# print(f"User ID: {user_id}, Alasan: {reason}")

# Memeriksa apakah pengguna adalah admin
# is_admin = await arg_handler.getAdmin(message)
# print(f"Apakah admin? {is_admin}")
```

### 3. Bing Image Generator (`bing`)

Membuat gambar berdasarkan prompt teks menggunakan layanan Bing Image Creator.

**Catatan:** Anda perlu menyediakan cookie otentikasi (`_U` dan `SRCHHPGUSR`) dari akun Microsoft Anda yang telah login ke Bing.

**Contoh Penggunaan:**

```python
import asyncio
from nsdev import ImageGenerator

# Cookie bisa didapatkan dari browser Anda setelah login ke Bing.
# Tekan F12 -> Application -> Cookies -> https://www.bing.com
auth_cookie_u = "YOUR_AUTH_COOKIE_U"
auth_cookie_srchhpgusr = "YOUR_SRCHHPGUSR_COOKIE"

async def main():
    try:
        bing = ImageGenerator(auth_cookie_u, auth_cookie_srchhpgusr)
        
        prompt = "Kucing astronot mengendarai roket di luar angkasa"
        # Hasilkan 2 gambar
        images = await bing.generate(prompt, num_images=2)
        
        print("Gambar berhasil dibuat:")
        for img_url in images:
            print(img_url)
            
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Telegram Button Builder (`button`)

Kelas untuk membuat keyboard Pyrogram (`InlineKeyboardMarkup` dan `ReplyKeyboardMarkup`) dengan mudah dari sintaks teks khusus.

**Contoh Penggunaan:**

```python
from nsdev import Button

btn_builder = Button()

# 1. Membuat Inline Keyboard
text_with_inline_buttons = """
Ini adalah teks utama.
| Tombol 1 - data_callback_1 |
| Tombol URL - https://google.com |
| Tombol Sebaris 1 - data1 | | Tombol Sebaris 2 - data2;same |
"""

# keyboard, remaining_text = btn_builder.create_keyboard(text_with_inline_buttons)
# client.send_message(chat_id, remaining_text, reply_markup=keyboard)


# 2. Membuat Reply Keyboard
text_with_reply_buttons = """
Pilih salah satu menu di bawah ini.
| Menu 1 - Menu 2 - Menu 3 |
"""
# keyboard, remaining_text = btn_builder.create_reply_keyboard(text_with_reply_buttons)
# client.send_message(chat_id, remaining_text, reply_markup=keyboard)
```

### 5. ANSI Colors (`colorize`)

Menyediakan koleksi konstanta warna ANSI untuk memformat output di terminal.

**Contoh Penggunaan:**

```python
from nsdev import AnsiColors

colors = AnsiColors()

print(f"{colors.GREEN}Ini adalah teks hijau.{colors.RESET}")
print(f"{colors.LIGHT_BLUE}Ini adalah teks biru muda.{colors.RESET}")
print(f"{colors.RED}Pesan error!{colors.RESET}")

# Mencetak semua warna yang tersedia
colors.print_all_colors()
```

### 6. Universal Database (`database`)

Handler database yang fleksibel dengan dukungan untuk penyimpanan lokal (JSON), MongoDB, dan SQLite. Data dienkripsi secara otomatis.

**Contoh Penggunaan:**

```python
from nsdev import DataBase

# 1. Penyimpanan Lokal (JSON)
db_local = DataBase(storage_type="local", file_name="my_app_data")

# 2. Penyimpanan MongoDB
# db_mongo = DataBase(storage_type="mongo", mongo_url="YOUR_MONGO_CONNECTION_STRING")

# 3. Penyimpanan SQLite
# db_sqlite = DataBase(storage_type="sqlite", file_name="my_sqlite_db")

# ---- Operasi Umum ----
db = db_local 
user_id = 12345

# Menyimpan variabel
db.setVars(user_id, "NAMA_PENGGUNA", "Andi")
db.setVars(user_id, "LEVEL", 10)

# Mendapatkan variabel
nama = db.getVars(user_id, "NAMA_PENGGUNA")
print(f"Nama pengguna: {nama}")

# Menyimpan daftar (list)
db.setListVars(user_id, "HOBI", "Membaca")
db.setListVars(user_id, "HOBI", "Berenang")

# Mendapatkan daftar
hobi = db.getListVars(user_id, "HOBI")
print(f"Hobi: {hobi}")

# Mengelola masa aktif pengguna
db.setExp(user_id, exp=30) # Atur kedaluwarsa dalam 30 hari
sisa_hari = db.daysLeft(user_id)
print(f"Masa aktif sisa: {sisa_hari} hari")

# Menyimpan kredensial bot
db.saveBot(user_id, api_id="123", api_hash="abc", value="YOUR_BOT_TOKEN", is_token=True)

# Menutup koneksi (penting untuk SQLite)
db.close()
```

### 7. Data Enkripsi (`encrypt`)

Menyediakan kelas `CipherHandler` untuk enkripsi dan dekripsi data sederhana dengan beberapa metode.

**Contoh Penggunaan:**

```python
from nsdev import CipherHandler

# Metode 'bytes' (default key dan delimiter)
cipher = CipherHandler(method="bytes", key=12345)

teks_asli = "Ini adalah data rahasia"

# Enkripsi
teks_terenkripsi = cipher.encrypt(teks_asli)
print(f"Terenkripsi: {teks_terenkripsi}")

# Dekripsi
teks_dekripsi = cipher.decrypt(teks_terenkripsi)
print(f"Terdekripsi: {teks_dekripsi}")
```

### 8. Gemini Chatbot (`gemini`)

Antarmuka untuk berinteraksi dengan model AI Google Gemini, baik untuk chatbot umum maupun untuk tugas spesifik seperti "cek khodam".

**Contoh Penggunaan:**

```python
from nsdev import ChatbotGemini

# Gunakan API key dari Google AI Studio
gemini = ChatbotGemini(api_key="YOUR_GEMINI_API_KEY")

# 1. Chatbot Umum
user_id = "user123"
bot_name = "Bot Keren"
pesan_pengguna = "Halo! Apa kabar?"

jawaban_bot = gemini.send_chat_message(pesan_pengguna, user_id, bot_name)
print(f"Jawaban Bot: {jawaban_bot}")

# 2. Cek Khodam (mode khusus)
nama = "Budi Santoso"
khodam_desc = gemini.send_khodam_message(nama)
print(f"\n--- Cek Khodam untuk {nama} ---")
print(khodam_desc)
```

### 9. Gradient & Terminal UI (`gradient`)

Membuat teks gradien artistik dan elemen UI seperti countdown di terminal.

**Contoh Penggunaan:**

```python
import asyncio
from nsdev import Gradient

ui = Gradient()

# 1. Menampilkan teks banner dengan gradien
ui.render_text("NORSODIKIN")

# 2. Menjalankan countdown asinkron
async def run_countdown():
    print("\nMemulai proses dalam...")
    await ui.countdown(10, text="Mohon tunggu {time}")
    print("\nProses selesai!")

if __name__ == "__main__":
    asyncio.run(run_countdown())
```

### 10. Logger Handler (`logger`)

Kelas logger yang canggih dengan output berwarna dan terformat, mencakup informasi waktu, level, modul, dan baris.

**Contoh Penggunaan:**

```python
from nsdev import LoggerHandler
import time

log = LoggerHandler()

def proses_data():
    log.info("Memulai proses data...")
    time.sleep(1)
    log.warning("Ada data yang tidak valid, namun proses dilanjutkan.")
    time.sleep(1)
    try:
        hasil = 10 / 0
    except Exception as e:
        log.error(f"Terjadi kesalahan fatal: {e}")
    
    log.debug("Proses data selesai.")

proses_data()
```

### 11. Payment Gateways (`payment`)

Menyediakan klien untuk berinteraksi dengan beberapa gateway pembayaran populer di Indonesia.

**Contoh Penggunaan:**

```python
import asyncio
from nsdev.payment import PaymentMidtrans, PaymentTripay, VioletMediaPayClient

# 1. Midtrans
# midtrans = PaymentMidtrans(server_key="YOUR_SERVER_KEY", client_key="YOUR_CLIENT_KEY")
# response = midtrans.createPayment(order_id="ORDER-123", gross_amount=50000)
# print(f"Midtrans redirect URL: {response.get('redirect_url')}")

# 2. Tripay
# tripay = PaymentTripay(api_key="YOUR_TRIPAY_API_KEY")
# response = tripay.createPayment(method="QRIS", amount=50000, order_id="ORDER-123", customer_name="Pelanggan")
# print(f"Tripay checkout URL: {response.data.checkout_url}")

# 3. VioletMediaPay (Async)
async def create_violet_payment():
    violet = VioletMediaPayClient(api_key="YOUR_VIOLET_API_KEY", secret_key="YOUR_VIOLET_SECRET_KEY")
    try:
        response = await violet.create_payment(amount="50000", produk="Pembelian Item")
        print("VioletMediaPay Response:")
        print(f"  - QR Image: {response.api_response['data']['qr_image']}")
        print(f"  - Ref Kode: {response.ref_kode}")
    except Exception as e:
        print(f"Error: {e}")

# asyncio.run(create_violet_payment())
```

### 12. Key Manager (`storekey`)

Menyimpan dan membaca kunci (misalnya, kunci API) secara aman di file sementara. Jika kunci tidak ada, ia akan meminta input dari pengguna.

**Contoh Penggunaan (dalam sebuah skrip):**

```python
from nsdev import KeyManager

# Inisialisasi manajer
key_manager = KeyManager()

# Membaca key dan env.
# Jika file tidak ada, akan meminta input pengguna.
# Jika dijalankan dengan argumen --key dan --env, akan menyimpan nilai tersebut.
# Contoh: python script.py --key 12345 --env MY_APP
key, env_name = key_manager.handle_arguments()

print(f"Key yang digunakan: {key}")
print(f"Nama environment: {env_name}")

# Logika aplikasi Anda selanjutnya menggunakan key dan env_name
```

### 13. YAML Reader (`ymlreder`)

Memuat file YAML dan mengubahnya menjadi objek `SimpleNamespace` agar mudah diakses menggunakan notasi titik (`.`).

**Contoh Penggunaan:**

Misalkan Anda memiliki file `config.yml`:

```yaml
database:
  host: localhost
  port: 5432
  user: admin

api_keys:
  telegram: "xyz-abc"
```

Kemudian di Python:

```python
from nsdev import YamlHandler

yaml_reader = YamlHandler()
config = yaml_reader.loadAndConvert("config.yml")

if config:
    print(f"Host Database: {config.database.host}")
    print(f"Port Database: {config.database.port}")
    print(f"Kunci API Telegram: {config.api_keys.telegram}")
```
