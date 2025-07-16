# VVIP Bot

Sebuah bot Telegram canggih yang dirancang untuk mengelola dan mengotomatiskan akses ke grup VVIP eksklusif Anda. Bot ini dilengkapi dengan proses pembayaran yang mulus menggunakan QRIS, verifikasi otomatis, dan panel kontrol yang komprehensif untuk pemilik.

## Fitur

- **Panel Kontrol Pemilik**: Tambah, hapus, dan kelola paket VVIP dengan mudah melalui menu interaktif.
- **Manajemen Member**: Lihat daftar semua anggota VVIP yang telah bergabung, lengkap dengan detail kategori, tanggal masuk, dan tombol untuk menendang (kick) member jika diperlukan.
- **Fitur Broadcast**: Kirim pesan massal (teks, gambar, dll.) ke semua pengguna yang pernah memulai bot, cocok untuk pengumuman penting atau promosi.
- **Harga Dinamis**: Atur harga normal dan harga promosi untuk setiap paket VVIP Anda.
- **Pesan yang Dapat Disesuaikan**: Sesuaikan teks deskripsi untuk setiap paket VVIP dan promosi.
- **Pembayaran QRIS Otomatis**: Terintegrasi dengan VioletMediaPay untuk menghasilkan kode QRIS unik untuk setiap transaksi.
- **Verifikasi Otomatis**: Bot secara otomatis memeriksa status pembayaran dan memberikan akses setelah pembayaran berhasil.
- **Pelacakan Pengguna**: Memberi tahu pemilik tentang pengguna baru yang memulai bot.
- **Akses Aman**: Mengirimkan tautan grup sebagai konten yang dilindungi setelah pembayaran berhasil.
- **Pemulihan Database**: Pulihkan seluruh database bot (pengguna, kategori, member) dari file backup `.zip` dengan satu perintah sederhana.

## Pengaturan dan Instalasi

Ikuti langkah-langkah ini untuk menjalankan bot VVIP Anda.

### 1. Prasyarat

- Python 3.8 atau lebih tinggi.
- Token Bot Telegram.
- API ID dan API Hash dari Telegram.
- API Key dan Secret Key dari VioletMediaPay.

### 2. Kloning Repositori

Pertama, kloning repositori ini ke mesin lokal atau server Anda.

```bash
git clone https://github.com/your-username/vvip.git
cd vvip
```

### 3. Instalasi Dependensi

Instal semua pustaka Python yang diperlukan menggunakan file `requirements.txt`.

```bash
pip3 install -r requirements.txt
```

### 4. Konfigurasi

Bot ini memerlukan file konfigurasi yang berisi kunci API dan pengaturan Anda. Sebuah skrip `config.sh` telah disediakan untuk mempermudah proses ini.

1.  Jalankan skrip tersebut. Skrip ini akan meminta Anda untuk memasukkan nilai-nilai yang diperlukan dan akan menyimpannya dalam sebuah file environment.
    ```bash
    bash config.sh
    ```
    Skrip akan meminta informasi berikut:
    - `API_ID`: API ID Telegram Anda.
    - `API_HASH`: API Hash Telegram Anda.
    - `BOT_TOKEN`: Token Bot Telegram Anda.
    - `OWNER_ID`: ID Pengguna Telegram numerik Anda.
    - `VIOLET_API_KEY`: API Key Anda dari VioletMediaPay.
    - `VIOLET_SECRET_KEY`: Secret Key Anda dari VioletMediaPay.
    - `Filename`: Nama yang ingin Anda berikan pada file environment Anda (contoh: `mybot.env`).


### 5. Menjalankan Bot

Setelah file konfigurasi dibuat, Anda dapat memulai bot.

Gunakan perintah berikut, ganti `nama_env` dengan nama file environment yang Anda buat pada langkah sebelumnya.

```bash
python3 vvip.py nama_env
```

**Contoh:**

- Jika file environment Anda bernama `.env`:
  ```bash
  python3 vvip.py .env
  ```
  Atau cukup (karena `.env` adalah default):
  ```bash
  python3 vvip.py
  ```

- Jika Anda menamai file environment Anda `mybot.env`:
  ```bash
  python3 vvip.py mybot.env
  ```

Bot sekarang akan dimulai, dan Anda akan melihat pesan konfirmasi di terminal Anda.

## Penggunaan Bot

### Untuk Pemilik

1.  Mulai bot dengan mengirimkan perintah `/start`.
2.  Anda akan melihat menu khusus pemilik dengan tombol **"⚙️ Panel Pengaturan ⚙️"**.
3.  Dari panel pengaturan, Anda dapat:
    - **Tambah Kategori VVIP**: Memandu Anda melalui proses penambahan paket baru. Anda akan diminta untuk memasukkan:
      - Nama Kategori
      - Harga Normal
      - Link Grup Normal
      - **Chat ID Normal**: ID numerik dari grup/channel. **Penting:** Ini digunakan untuk fitur tendang (kick). Untuk mendapatkannya, teruskan (forward) pesan dari channel/grup target ke bot seperti `@userinfobot`. Contoh: `-100123456789`.
      - Harga Promo (opsional)
      - Link Grup Promo dan **Chat ID Promo** (jika harga promo diisi)
      - Teks deskripsi normal dan promo.
    - **Hapus Kategori VVIP**: Menghapus paket VVIP yang sudah ada.
    - **Cek Member VVIP**: Menampilkan daftar semua member yang telah bergabung melalui bot. Daftar ini dipaginasi (dibagi per halaman) dan setiap entri member memiliki tombol untuk menendang mereka dari grup/channel VVIP yang sesuai.
    - **Buat Broadcast**: Mengirim pesan ke semua pengguna yang pernah memulai bot Anda. Cukup kirimkan pesan apa pun (teks, gambar, video, dll) setelah menekan tombol ini, dan bot akan menyiarkannya.
- **Pulihkan Database (`/restore`)**: Bot secara otomatis membuat backup database secara berkala. Untuk memulihkan data, balas (reply) file backup `.zip` yang dikirimkan bot ke chat Anda, lalu kirimkan perintah `/restore`. **PENTING: Restart bot setelah proses ini selesai agar data yang dipulihkan dapat digunakan.**

### Untuk Pengguna

1.  Pengguna memulai bot dengan perintah `/start`. Mereka akan disambut dengan menu utama yang berisi tombol-tombol fungsional.
2.  Mereka dapat mengklik **"📚 Lihat Daftar VVIP 📚"** untuk melihat semua paket yang tersedia.
3.  Tombol **"ℹ️ Tentang Bot ℹ️"** juga tersedia untuk memberikan panduan singkat dan penjelasan mengenai cara kerja bot.
4.  Mereka dapat melihat detail untuk paket harga normal atau promo.
5.  Dengan mengklik tombol "Bayar", mereka akan menerima kode QRIS unik untuk menyelesaikan pembayaran.
6.  Setelah pembayaran berhasil diverifikasi oleh bot, mereka akan secara otomatis menerima tautan untuk bergabung ke grup VVIP.

#### ⭐️ Create: [@NorSodikin](https://t.me/NorSodikin)
