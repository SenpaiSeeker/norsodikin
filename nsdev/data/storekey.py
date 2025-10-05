import argparse
import sys

import setproctitle

from ..utils.logger import LoggerHandler


class KeyManager:
    def __init__(self):
        self.logger = LoggerHandler()

    def handle_arguments(self):
        parser = argparse.ArgumentParser(
            description="Pemuat konfigurasi skrip.",
            epilog="Argumen --key dan --env wajib disertakan untuk menjalankan skrip.",
        )
        parser.add_argument("--key", type=str, help="Kunci rahasia untuk enkripsi data.")
        parser.add_argument("--env", type=str, help="Nama file environment yang akan dimuat (contoh: .env).")
        args = parser.parse_args()

        if not args.key or not args.env:
            self.logger.print(f"{self.logger.RED}Argumen --key dan --env harus disertakan untuk menjalankan bot.")
            self.logger.print(
                f"{self.logger.YELLOW}Contoh: python3 -m NSUserBot --key kunci-rahasia-anda --env robot.env"
            )
            sys.exit(1)

        self.hide_sensitive_args()

        self.logger.print(f"{self.logger.GREEN}Berhasil memuat kunci dan file environment dari argumen baris perintah.")
        return args.key, args.env

    def hide_sensitive_args(self):
        original_argv = sys.argv
        cleaned_argv = []
        skip_next = False

        for i, arg in enumerate(original_argv):
            if skip_next:
                skip_next = False
                continue

            if arg == "--key":
                cleaned_argv.append(arg)
                cleaned_argv.append("[REDACTED]")
                if i + 1 < len(original_argv):
                    skip_next = True
            else:
                cleaned_argv.append(arg)

        try:
            setproctitle.setproctitle(" ".join(cleaned_argv))
        except Exception as e:
            self.logger.print(f"{self.logger.YELLOW}Gagal menyembunyikan argumen proses: {e}")
