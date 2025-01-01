class KeyManager:
    def __init__(self):
        self.argparse = __import__("argparse")
        self.tempfile = __import__("tempfile")
        self.os = __import__("os")
        self.log = __import__("nsdev").logger.LoggerHandler()
        self.temp_file = self.os.path.join(self.tempfile.gettempdir(), "temp_key.txt")

    def save_key(self, key):
        try:
            with open(self.temp_file, "w") as f:
                f.write(key)
            self.log.info(f"Key '{key}' telah disimpan.")
            return key
        except OSError as e:
            self.log.error(f"Terjadi kesalahan saat menyimpan key: {e}")
            return None

    def read_key(self):
        if self.os.path.exists(self.temp_file):
            try:
                with open(self.temp_file, "r") as f:
                    saved_key = f.read().strip()
                self.log.debug(f"Key terakhir yang disimpan: {saved_key}")
                return saved_key
            except OSError as e:
                self.log.error(f"Terjadi kesalahan saat membaca key: {e}")
                return None
        else:
            self.log.warning("Tidak ada key yang disimpan. Jalankan ulang program dengan --key atau --new-key.")
            return None

    def handle_arguments(self):
        parser = self.argparse.ArgumentParser()
        parser.add_argument("--key", type=str)
        parser.add_argument("--new-key", type=str)
        args = parser.parse_args()

        if args.key:
            return self.save_key(args.key)
        elif args.new_key:
            return self.save_key(args.new_key)
        else:
            return self.read_key()
