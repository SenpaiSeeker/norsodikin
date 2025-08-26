# Panduan Instalasi dan Penggunaan Ollama di VPS

Selamat datang di panduan instalasi Ollama! Dokumen ini akan memandu Anda untuk memasang dan menjalankan model AI canggih secara lokal di Virtual Private Server (VPS) Anda, sehingga dapat digunakan oleh modul `client.ns.ai.local()` dari pustaka `norsodikin`.

Menjalankan AI secara lokal memberikan keuntungan besar seperti privasi penuh, tanpa biaya per-permintaan API, dan kontrol total atas model yang Anda gunakan.

## Persyaratan

*   Sebuah VPS yang menjalankan sistem operasi Linux (Direkomendasikan **Ubuntu 22.04** atau lebih baru).
*   Akses root atau pengguna dengan hak `sudo`.
*   **Spesifikasi VPS Minimum yang Direkomendasikan:**
    *   **RAM:** 8 GB (Untuk model ringan seperti `phi3:mini` atau `mistral`)
    *   **RAM:** 16 GB (Untuk model yang lebih besar seperti `llama3:8b` dengan lebih nyaman)
    *   **CPU:** 4 Core atau lebih.
    *   **Penyimpanan:** Setidaknya 30 GB ruang kosong.

---

## Langkah 1: Instalasi Ollama

Ollama menyediakan skrip instalasi yang sangat memudahkan prosesnya.

1.  Masuk ke VPS Anda melalui SSH.
2.  Jalankan perintah berikut di terminal. Perintah ini akan mengunduh dan menginstal Ollama secara otomatis.
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
3.  Setelah instalasi selesai, Ollama akan berjalan sebagai *service* di latar belakang. Anda bisa memverifikasi statusnya dengan perintah:
    ```bash
    systemctl status ollama
    ```
    Jika outputnya menunjukkan `active (running)`, berarti Ollama sudah siap.
4.  (Opsional tapi direkomendasikan) Aktifkan Ollama agar otomatis berjalan setiap kali VPS di-reboot:
    ```bash
    sudo systemctl enable ollama
    ```

---

## Langkah 2: Unduh Model AI

Setelah Ollama terpasang, Anda perlu mengunduh "otak" atau model AI yang ingin Anda gunakan.

1.  Pilih model yang sesuai dengan spesifikasi VPS Anda. Berikut beberapa rekomendasi:
    *   **`phi3:mini`** (Sangat direkomendasikan untuk VPS 8GB RAM): Cerdas, cepat, dan hanya membutuhkan ~2.3 GB RAM saat aktif.
    *   **`mistral`** (Pilihan bagus untuk 8GB RAM): Sedikit lebih berat dari Phi-3, membutuhkan ~4.1 GB RAM.
    *   **`llama3:8b`** (Direkomendasikan untuk 16GB RAM): Sangat powerful, tapi membutuhkan ~4.7 GB RAM.

2.  Jalankan perintah `ollama run` untuk mengunduh model pilihan Anda. Contoh untuk `phi3:mini`:
    ```bash
    ollama run phi3:mini
    ```
    Perintah ini akan memulai proses unduh. Setelah selesai, Anda akan masuk ke mode chat interaktif di terminal. Anda bisa mengetik sesuatu untuk menguji modelnya.

3.  Untuk keluar dari mode chat interaktif, ketik `/bye` dan tekan Enter.

4.  Anda bisa mengunduh beberapa model sekaligus. Untuk melihat daftar model yang sudah Anda unduh, gunakan perintah:
    ```bash
    ollama list
    ```

---

## Langkah 3: (WAJIB) Buat SWAP File untuk Stabilitas

Untuk mencegah VPS Anda crash karena kehabisan RAM saat model AI bekerja keras, sangat penting untuk membuat SWAP file. Ini berfungsi sebagai "RAM cadangan" yang menggunakan ruang disk.

1.  Buat SWAP file (contoh ini membuat SWAP sebesar 8 GB, sesuaikan jika perlu).
    ```bash
    sudo fallocate -l 8G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    ```
2.  Buat SWAP menjadi permanen agar aktif otomatis setelah reboot.
    ```bash
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    ```
3.  Verifikasi bahwa SWAP sudah aktif dengan perintah `free -h`. Anda akan melihat baris `Swap` dengan ukuran yang Anda buat.

---

Sekarang Ollama sudah terinstal, model sudah diunduh, dan sistem Anda stabil dengan SWAP. Layanan Ollama berjalan di `http://localhost:11434` dan siap menerima perintah dari bot `norsodikin` Anda melalui `client.ns.ai.local()`.
