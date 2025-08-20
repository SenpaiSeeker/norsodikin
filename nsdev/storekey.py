class KeyManager:
    def __init__(self):
        self.sys = __import__("sys")
        self.argparse = __import__("argparse")
        nsdev = __import__("nsdev")
        self.logger = nsdev.logger.LoggerHandler()

    def handle_arguments(self):
        parser = self.argparse.ArgumentParser(
            description="Pemuat konfigurasi skrip.",
            epilog="Argumen --key dan --env wajib disertakan untuk menjalankan skrip.",
        )
        parser.add_argument("--key", type=str, help="Kunci rahasia untuk enkripsi data.")
        parser.add_argument("--env", type=str, help="Nama file environment yang akan dimuat (contoh: .env).")
        args = parser.parse_args()

        if not args.key or not args.env:
            self.logger.print(f"{self.logger.RED}Argumen --key dan --env harus disertakan untuk menjalankan bot.")
            self.logger.print(f"{self.logger.YELLOW}Contoh: python3 main.py --key kunci-rahasia-anda --env robot.env")
            self.sys.exit(1)

        self.logger.print(f"{self.logger.GREEN}Berhasil memuat kunci dan file environment dari argumen baris perintah.")
        return args.key, args.env
