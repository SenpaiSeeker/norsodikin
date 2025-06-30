class CipherHandler:
    def __init__(self, **options):
        """
        Inisialisasi CipherHandler dengan opsi konfigurasi.

        :param options:
            - method (str): Metode enkripsi yang digunakan. Pilihan: 'shift', 'bytes', 'binary'. Default: 'shift'.
            - key (int | list[int]): Kunci enkripsi/dekripsi. Default: 31099.
            - delimiter (str): Delimiter yang digunakan untuk metode 'shift'. Default: '|'.
        """
        self.log = __import__("nsdev").logger.LoggerHandler()
        self.method = options.get("method", "shift")
        self.key = self._normalize_key(options.get("key", 31099))
        self.delimiter = options.get("delimiter", "|")

    def _normalize_key(self, key):
        try:
            if isinstance(key, list):
                return int("".join(map(str, key)))
            elif isinstance(key, int):
                return key
            else:
                raise ValueError("Key must be an integer or a list of integers.")
        except Exception as e:
            raise ValueError(f"Key normalization failed: {e}")

    def _offset(self, index):
        try:
            return len(str(self.key)) * (index + 1)
        except Exception as e:
            raise Exception(f"Offset calculation failed at index {index}: {e}")

    def _xor_encrypt_decrypt(self, data: bytes) -> bytes:
        key_bytes = self.key.to_bytes((self.key.bit_length() + 7) // 8, byteorder="big")

        if isinstance(data, str):
            data = data.encode("utf-8")

        return bytes([data[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data))])

    def decrypt(self, encrypted_data: str) -> str:
        if self.method == "bytes":
            return self.decrypt_bytes(encrypted_data)
        elif self.method == "binary":
            return self.decrypt_binary(encrypted_data)
        elif self.method == "shift":
            return self.decrypt_shift(encrypted_data)
        else:
            raise ValueError(f"Metode dekripsi '{self.method}' tidak dikenali.")

    def decrypt_binary(self, encrypted_bits: str) -> str:
        if len(encrypted_bits) % 8 != 0:
            raise ValueError("Data biner yang dienkripsi tidak valid.")
        decrypted_chars = [chr(int(encrypted_bits[i : i + 8], 2) ^ (self.key % 256)) for i in range(0, len(encrypted_bits), 8)]
        return "".join(decrypted_chars)

    def decrypt_bytes(self, encrypted_data: str) -> str:
        try:
            codes = list(map(int, encrypted_data.split(self.delimiter)))
            return "".join(chr(code - self._offset(i)) for i, code in enumerate(codes))
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")

    def decrypt_shift(self, encoded_text: str) -> str:
        try:
            decoded = "".join(chr(int(code) - self.key) for code in encoded_text.split(self.delimiter))
            return decoded
        except ValueError as error:
            raise ValueError(f"Error during shift decryption: {error}")

    def encrypt(self, data: str) -> str:
        if self.method == "bytes":
            return self.encrypt_bytes(data)
        elif self.method == "binary":
            return self.encrypt_binary(data)
        elif self.method == "shift":
            return self.encrypt_shift(data)
        else:
            raise ValueError(f"Metode enkripsi '{self.method}' tidak dikenali.")

    def encrypt_binary(self, plaintext: str) -> str:
        encrypted_bits = "".join(format(ord(char) ^ (self.key % 256), "08b") for char in plaintext)
        return encrypted_bits

    def encrypt_bytes(self, message: str) -> str:
        try:
            encrypted_values = [str(ord(char) + self._offset(i)) for i, char in enumerate(message)]
            return self.delimiter.join(encrypted_values)
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")

    def encrypt_shift(self, text: str) -> str:
        encoded = self.delimiter.join(str(ord(char) + self.key) for char in text)
        return encoded

    def save(self, filename: str, code: str):
        encrypted_code = self.encrypt(code)
        if encrypted_code is None:
            raise ValueError("Encryption failed.")
        result = f"exec(__import__('nsdev').CipherHandler(method='{self.method}', key={self.key}).decrypt('{encrypted_code}'))"
        try:
            with open(filename, "w") as file:
                file.write(result)
            self.log.info(f"Kode berhasil disimpan ke file {filename}")
        except Exception as e:
            raise IOError(f"Saving file failed: {e}")


class AsciiManager(__import__("nsdev").AnsiColors):
    def __init__(self, key):
        super().__init__()
        try:
            self.no_format_key = key
            self.key = self._normalize_key(self.no_format_key)
        except Exception as e:
            raise Exception(f"Initialization failed: {e}")

    def _normalize_key(self, key):
        try:
            if isinstance(key, list):
                return int("".join(map(str, key)))
            elif isinstance(key, int):
                return key
            else:
                raise Exception("Key must be an integer or a list of integers.")
        except Exception as e:
            raise Exception(f"Key normalization failed: {e}")

    def _offset(self, index):
        try:
            return len(str(self.key)) * (index + 1)
        except Exception as e:
            raise Exception(f"Offset calculation failed at index {index}: {e}")

    def encrypt(self, message):
        try:
            return [int(ord(char) + self._offset(i)) for i, char in enumerate(message)]
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")

    def decrypt(self, encrypted):
        try:
            return "".join(chr(int(code) - self._offset(i)) for i, code in enumerate(encrypted))
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")

    def save_data(self, filename, code):
        try:
            with open(filename, "w") as file:
                result = f"exec(__import__('nsdev').AsciiManager({self.no_format_key}).decrypt({self.encrypt(code)}))"
                file.write(result)
                print(f"{self.GREEN}Kode berhasil disimpan ke file {filename}")
        except Exception as e:
            raise Exception(f"Failed to save data to {filename}: {e}")
