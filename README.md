# Pustaka Python `norsodikin`

[![Lisensi: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Selamat datang di `norsodikin`! Ini bukan sekadar pustaka Python biasa, melainkan sebuah toolkit serbaguna yang dirancang untuk menyederhanakan tugas-tugas kompleks seperti pengembangan bot Telegram, manajemen server Linux, enkripsi data, hingga integrasi dengan berbagai layanan AI.

**Fitur Unggulan**: Pustaka ini terintegrasi penuh dengan `Pyrogram`. Semua fungsionalitas dapat diakses secara intuitif melalui `client.ns`, menjadikan kode bot Anda lebih bersih, terstruktur, dan mudah dikelola.

## Instalasi

Instalasi `norsodikin` dilakukan langsung dari repositori GitHub untuk memastikan Anda mendapatkan versi terkini.

**1. Instalasi Lengkap**

Perintah ini menginstal `norsodikin` beserta `Pyrogram` dan semua dependensi yang diperlukan untuk menjalankan fitur-fitur seperti AI, media downloader, dan manajemen server. Ini adalah metode yang paling direkomendasikan.

```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin[all]"
```

> **Catatan Penting untuk Fitur AI:**
> Beberapa fitur memerlukan library sistem. Pada Debian/Ubuntu, instal dengan:
> ```bash
> sudo apt-get update && sudo apt-get install -y libzbar0 ffmpeg
> ```

**2. Instalasi Pustaka Saja (Tanpa Pyrogram)**

Gunakan perintah ini jika Anda hanya ingin menggunakan utilitas `norsodikin` di luar proyek Pyrogram.

```bash
pip3 install "git+https://github.com/SenpaiSeeker/norsodikin#egg=norsodikin"
```

## Konsep Dasar & Integrasi Pyrogram

Keajaiban `norsodikin` terletak pada integrasi `monkey-patching` yang mulus dengan Pyrogram. Cukup dengan mengimpor `nsdev` sekali di skrip utama Anda, semua fungsionalitas akan otomatis "menempel" pada objek `client` Anda melalui namespace `ns`.

Semua modul dikelompokkan secara logis:
- `client.ns.ai`: Semua yang berhubungan dengan Kecerdasan Buatan.
- `client.ns.analytics`: Analitik penggunaan bot dan statistik chat.
- `client.ns.auth`: Manajemen pengguna dan hak akses (peran).
- `client.ns.telegram`: Utilitas spesifik untuk Telegram (tombol, format teks, dll.).
- `client.ns.data`: Manajemen data (database, file config YAML).
- `client.ns.utils`: Perkakas umum (logger, downloader, OSINT, pastebin, dll.).
- `client.ns.schedule`: Penjadwalan tugas otomatis (cron).
- `client.ns.server`: Manajemen server Linux (proses, monitor).
- `client.ns.code`: Enkripsi dan dekripsi.
- `client.ns.payment`: Integrasi payment gateway.
- `client.ns.tempmail`: Generate temporary mail.

**Struktur Kode Dasar**:

```python
import pyrogram
import nsdev  # Voila! Integrasi .ns langsung aktif untuk pyrogram.Client

# Asumsikan 'client' adalah instance dari pyrogram.Client
# client = pyrogram.Client(...)

# Sekarang, semua modul siap pakai dalam namespace masing-masing:
client.ns.utils.log.info("Logger canggih siap mencatat progres bot!")

# Contoh memuat konfigurasi dari file .yml
# config = client.ns.data.yaml.loadAndConvert("config.yml")
# api_key = config.api.gemini_key
```
---
## Lisensi

Pustaka ini dirilis di bawah [Lisensi MIT](https://opensource.org/licenses/MIT). Artinya, Anda bebas menggunakan, memodifikasi, dan mendistribusikan kode ini untuk proyek komersial maupun non-komersial.

---

Semoga dokumentasi yang komprehensif ini membuat pengalaman pengembangan Anda menjadi lebih mudah dan menyenangkan. Selamat mencoba dan berkreasi dengan `norsodikin`! Jika ada pertanyaan atau butuh bantuan, jangan ragu untuk kontak di [Telegram](https://t.me/NorSodikin).
