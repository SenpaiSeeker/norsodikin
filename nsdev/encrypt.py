class CipherHandler:
    def __init__(self, **options):
        """
        Inisialisasi CipherHandler dengan opsi konfigurasi.

        :param options:
            - method (str): Metode enkripsi yang digunakan. Pilihan: 'shift', 'bytes', 'binary'. Default: 'shift'.
            - key (int): Kunci enkripsi/dekripsi. Default: 31099.
            - delimiter (str): Delimiter yang digunakan untuk metode 'shift'. Default: '|'.
        """
        self.method: str = options.get("method", "shift")
        self.key: int = options.get("key", 31099)
        self.delimiter: str = options.get("delimiter", "|")
        self.log = __import__("nsdev").logger.LoggerHandler()

    def _xor_encrypt_decrypt(self, data: bytes) -> bytes:
        key_bytes = self.key.to_bytes((self.key.bit_length() + 7) // 8, byteorder="big")
        return bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])

    def encrypt_bytes(self, data: str) -> str:
        serialized_data = __import__("textwrap").dedent(data).encode("utf-8")
        encrypted_data = self._xor_encrypt_decrypt(serialized_data)
        return __import__("base64").urlsafe_b64encode(encrypted_data).decode("utf-8").rstrip("=")

    def decrypt_bytes(self, encrypted_data: str) -> str:
        try:
            if len(encrypted_data) % 4 != 0:
                encrypted_data += "=" * (4 - len(encrypted_data) % 4)
            encrypted_bytes = __import__("base64").urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted_bytes = self._xor_encrypt_decrypt(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as error:
            self.log.error(f"Decrypt bytes error: {error}")
            return ""

    def encrypt_binary(self, plaintext: str) -> str:
        return "".join(format(ord(char) ^ (self.key % 256), "08b") for char in plaintext)

    def decrypt_binary(self, encrypted_bits: str) -> str:
        if len(encrypted_bits) % 8 != 0:
            self.log.error("Data biner yang dienkripsi tidak valid.")
            return ""
        return "".join(chr(int(encrypted_bits[i : i + 8], 2) ^ (self.key % 256)) for i in range(0, len(encrypted_bits), 8))

    def encrypt_shift(self, text: str) -> str:
        return self.delimiter.join(str(ord(char) + self.key) for char in text)

    def decrypt_shift(self, encoded_text: str) -> str:
        try:
            return "".join(chr(int(code) - self.key) for code in encoded_text.split(self.delimiter))
        except ValueError as error:
            self.log.error(f"Decrypt shift error: {error}")
            return ""

    def encrypt(self, data: str) -> str:
        if self.method == "bytes":
            return self.encrypt_bytes(data)
        elif self.method == "binary":
            return self.encrypt_binary(data)
        elif self.method == "shift":
            return self.encrypt_shift(data)
        else:
            self.log.error(f"Metode enkripsi '{self.method}' tidak dikenali.")
            return ""

    def decrypt(self, encrypted_data: str) -> str:
        if self.method == "bytes":
            return self.decrypt_bytes(encrypted_data)
        elif self.method == "binary":
            return self.decrypt_binary(encrypted_data)
        elif self.method == "shift":
            return self.decrypt_shift(encrypted_data)
        else:
            self.log.error(f"Metode dekripsi '{self.method}' tidak dikenali.")
            return ""

    def save(self, filename: str, code: str):
        try:
            encrypted_code = self.encrypt(code)
            result = f"exec(__import__('nsdev').CipherHandler(method='{self.method}', key={self.key}).decrypt('{encrypted_code}'))"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(result)
            self.log.info(f"Kode berhasil disimpan ke file {filename}")
        except Exception as e:
            self.log.error(f"Error saat menyimpan file: {e}")
