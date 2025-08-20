class KeyManager:
    def __init__(self):
        self.os = __import__("os")
        self.sys = __import__("sys")
        self.json = __import__("json")
        self.argparse = __import__("argparse")
        self.logger = __import__("nsdev").logger.LoggerHandler()
        self.cache_file = self.os.path.join(self.os.getcwd(), ".app_cache")

    def handle_arguments(self):
        parser = self.argparse.ArgumentParser(
            description="Pemuat konfigurasi.",
            add_help=False,
        )
        parser.add_argument("--key", type=str, help="Kunci rahasia untuk enkripsi data.")
        parser.add_argument("--env", type=str, help="Nama file environment yang akan dimuat.")

        args, unknown = parser.parse_known_args()

        if args.key and args.env:
            cache_data = {"key": args.key, "env": args.env}
            try:
                with open(self.cache_file, "w") as f:
                    self.json.dump(cache_data, f)
            except Exception as e:
                self.logger.print(
                    f"{self.logger.RED}Duh, gagal nyimpen file cache. Folder ini kayaknya gak bisa ditulisi, coba cek dulu ya. Error: {e}"
                )
                self.sys.exit(1)
            return args.key, args.env

        elif self.os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    cache_data = self.json.load(f)
                return cache_data["key"], cache_data["env"]
            except Exception:
                self.logger.print(
                    f"{self.logger.RED}Waduh, file cache-nya kayaknya rusak. Coba jalanin lagi pakai `--key` dan `--env` buat benerin, ya."
                )
                self.sys.exit(1)

        else:
            self.logger.print(
                f"{self.logger.RED}Oh, ini baru pertama kali ya? Perlu di-setup dulu. Coba jalanin lagi pakai argumen `--key` dan `--env`."
            )
            self.sys.exit(1)
