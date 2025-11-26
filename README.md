# Pustaka Python `norsodikin`

[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan sebuah toolkit serbaguna yang dirancang untuk menyederhanakan tugas-tugas kompleks seperti pengembangan bot Telegram, manajemen server Linux, enkripsi data, hingga integrasi dengan berbagai layanan AI.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas dapat diakses secara intuitif melalui `client.ns`, menjadikan kode bot Anda lebih bersih, terstruktur, dan mudah dikelola.

## Instalasi

Instalasi `norsodikin` dilakukan langsung dari repositori GitHub untuk memastikan Anda mendapatkan versi terkini.

**1. Instalasi Lengkap (Direkomendasikan)**

Metode ini menginstal `norsodikin` beserta `Pyrogram` dan semua dependensi yang diperlukan untuk menjalankan fitur-fitur seperti AI, media downloader, dan manajemen server.

**Langkah 1: Instal Library Sistem**
Beberapa fitur AI dan rendering gambar memerlukan dependensi sistem. Pada sistem berbasis Debian/Ubuntu, jalankan:
```bash
sudo apt-get update && sudo apt-get install -y libzbar0 ffmpeg
```

**Langkah 2: Instal Pustaka Python**
```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[pyrogram]"
```

**Langkah 3: Instal Browser untuk Playwright**
Fitur pembuatan gambar dari teks (seperti `.q` atau `.tweet`) menggunakan browser *headless*. Instal browser yang diperlukan dengan perintah ini:
```bash
python3 -m playwright install --with-deps
```

**2. Instalasi Pustaka Saja (Tanpa Pyrogram)**

Gunakan perintah ini jika Anda hanya ingin menggunakan utilitas `norsodikin` di luar proyek Pyrogram.
```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin"
```

## Konsep Dasar & Integrasi Pyrogram

Keajaiban `norsodikin` terletak pada integrasi `monkey-patching` yang mulus dengan Pyrogram. Cukup dengan mengimpor `nsdev` sekali di skrip utama Anda, semua fungsionalitas akan otomatis "menempel" pada objek `client` Anda melalui namespace `ns`.

Semua modul dikelompokkan secara logis:
- `client.ns.ai`: Semua yang berhubungan dengan Kecerdasan Buatan (Gemini, Bing, OCR, TTS, dll.).
- `client.ns.analytics`: Analitik penggunaan bot dan statistik chat.
- `client.ns.auth`: Manajemen pengguna dan hak akses (peran).
- `client.ns.telegram`: Utilitas spesifik untuk Telegram (tombol, format teks, auto-action, dll.).
- `client.ns.data`: Manajemen data (database, file config YAML, enkripsi).
- `client.ns.utils`: Perkakas umum (logger, downloader, OSINT, pastebin, konversi media).
- `client.ns.schedule`: Penjadwalan tugas otomatis (cron).
- `client.ns.server`: Manajemen server Linux (proses, monitor, speedtest, SSH user).
- `client.ns.code`: Enkripsi dan dekripsi string/kode.
- `client.ns.payment`: Integrasi payment gateway (Midtrans, Tripay, Saweria, Cashify, Violet).
- `client.ns.tempmail`: Generator email sementara.
- `client.ns.pinterest`: Pencari dan pengunduh media Pinterest yang canggih.

**Struktur Kode Dasar**:

```python
import pyrogram
import nsdev  # Voila! Integrasi .ns langsung aktif untuk pyrogram.Client

# Asumsikan 'client' adalah instance dari pyrogram.Client
# client = pyrogram.Client(...)

# Sekarang, semua modul siap pakai dalam namespace masing-masing:
client.ns.utils.log.info("Logger canggih siap mencatat progres bot!")

# Contoh penggunaan fitur AI
# response = await client.ns.ai.gemini(api_key="...").send_chat_message("Halo AI!")

# Contoh penggunaan Pinterest
# images = await client.ns.pinterest.search("anime aesthetic")
```

## Fitur Baru: Pinterest Engine
Modul Pinterest kini lebih handal dengan engine khusus yang mendukung pencarian, unduhan gambar/video, dan penanganan media yang lebih baik untuk menghindari error format.

## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk proyek komersial maupun non-komersial.

---

Semoga dokumentasi yang komprehensif ini membuat pengalaman pengembangan Anda menjadi lebih mudah dan menyenangkan. Selamat mencoba dan berkreasi dengan `norsodikin`! Jika ada pertanyaan atau butuh bantuan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
