class KeyManager:
    def __init__(self, filename: str = "temp_key.txt"):
        self.argparse = __import__("argparse")
        self.tempfile = __import__("tempfile")
        self.os = __import__("os")
        self.sys = __import__("sys")
        self.logger = __import__("nsdev").logger.LoggerHandler()
        self.cipher = __import__("nsdev").encrypt.CipherHandler(method="bytes")
        self.temp_file = self.os.path.join(self.tempfile.gettempdir(), filename)

    def save_key(self, key):
        try:
            with open(self.temp_file, "w") as file:
                file.write(self.cipher.encrypt(key))
        except OSError as e:
            self.logger.error(f"Terjadi kesalahan saat menyimpan key: {e}")
            self.sys.exit(1)

    def read_key(self):
        if self.os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, "r") as file:
                    saved_key = self.cipher.decrypt(file.read().strip())
                return saved_key
            except OSError as e:
                self.logger.error(f"Terjadi kesalahan saat membaca key: {e}")
                self.sys.exit(1)
        else:
            self.logger.warning("Tidak ada key yang disimpan. Jalankan ulang program dengan --key")
            self.sys.exit(1)

    def handle_arguments(self):
        parser = self.argparse.ArgumentParser()
        parser.add_argument("--key", type=str, help="Key yang ingin disimpan atau digunakan.")
        args = parser.parse_args()

        return self.save_key(args.key) if args.key else self.read_key()
