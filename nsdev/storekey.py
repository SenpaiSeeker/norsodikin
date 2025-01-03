class KeyManager:
    def __init__(self, filename: str = "temp_key.txt"):
        self.argparse = __import__("argparse")
        self.tempfile = __import__("tempfile")
        self.os = __import__("os")
        self.sys = __import__("sys")
        nsdev = __import__("nsdev")

        self.logger = nsdev.logger.LoggerHandler()
        self.cipher = nsdev.encrypt.CipherHandler(method="bytes")

        self.temp_file = self.os.path.join(self.tempfile.gettempdir(), filename)

    def save_key(self, key: str):
        try:
            with open(self.temp_file, "w") as file:
                file.write(self.cipher.encrypt(key))
        except OSError as e:
            self._handle_error(f"Terjadi kesalahan saat menyimpan key: {e}")

    def read_key(self) -> str:
        try:
            with open(self.temp_file, "r") as file:
                return self.cipher.decrypt(file.read().strip())
        except FileNotFoundError:
            self._handle_warning("Tidak ada key yang disimpan. Jalankan ulang program dengan --key")
        except OSError as e:
            self._handle_error(f"Terjadi kesalahan saat membaca key: {e}")

    def handle_arguments(self) -> str:
        parser = self.argparse.ArgumentParser()
        parser.add_argument("--key", type=str, help="Key yang ingin disimpan atau digunakan.")
        args = parser.parse_args()

        if args.key:
            self.save_key(args.key)

        return self.read_key()

    def _handle_error(self, message: str):
        self.logger.error(message)
        self.sys.exit(1)

    def _handle_warning(self, message: str):
        self.logger.warning(message)
        self.sys.exit(1)
