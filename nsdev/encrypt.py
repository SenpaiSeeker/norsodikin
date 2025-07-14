class CipherHandler:
    def __init__(self, **options):
        self.log = __import__("nsdev").logger.LoggerHandler()

        self.method = options.get("method", "shift")
        self.key = self._normalize_key(options.get("key", "my_s3cr3t_k3y_@2024!"))
        self.numeric_key = self._get_numeric_key()
        self.delimiter = options.get("delimiter", "|")

        if not self.key:
            raise ValueError("Key cannot be empty.")

    def _normalize_key(self, key) -> str:
        try:
            if isinstance(key, list):
                return "".join(map(str, key))
            elif isinstance(key, (int, float)):
                return str(key)
            elif isinstance(key, str):
                return key
            else:
                return str(key)
        except Exception as e:
            raise ValueError(f"Key normalization failed: {e}")

    def _get_numeric_key(self) -> int:
        return sum(ord(c) for c in self.key)

    def _offset(self, index: int) -> int:
        try:
            key_char_code = ord(self.key[index % len(self.key)])
            return len(self.key) * (index + 1) + key_char_code
        except Exception as e:
            raise Exception(f"Offset calculation failed at index {index}: {e}")

    def _xor_encrypt_decrypt(self, data: bytes) -> bytes:
        key_bytes = self.key.encode("utf-8")
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
        if not encrypted_bits or len(encrypted_bits) % 8 != 0:
            raise ValueError("Data biner yang dienkripsi tidak valid atau kosong.")
        xor_key = self.numeric_key % 256
        decrypted_chars = [chr(int(encrypted_bits[i : i + 8], 2) ^ xor_key) for i in range(0, len(encrypted_bits), 8)]
        return "".join(decrypted_chars)

    def decrypt_bytes(self, encrypted_data: str) -> str:
        try:
            padding_needed = (4 - len(encrypted_data) % 4) % 4
            padded_data = encrypted_data + "=" * padding_needed

            decoded_b64 = __import__("base64").b64decode(padded_data).decode("utf-8")
            codes = list(map(int, decoded_b64.split(self.delimiter)))
            return "".join(chr(code - self._offset(i)) for i, code in enumerate(codes))
        except Exception as e:
            raise Exception(f"Decryption failed for 'bytes' method: {e}")

    def decrypt_shift(self, encoded_text: str) -> str:
        try:
            codes = encoded_text.split(self.delimiter)
            return "".join(chr(int(code, 16) - ord(self.key[i % len(self.key)])) for i, code in enumerate(codes))
        except (ValueError, TypeError) as error:
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
        xor_key = self.numeric_key % 256
        encrypted_bits = "".join(format(ord(char) ^ xor_key, "08b") for char in plaintext)
        return encrypted_bits

    def encrypt_bytes(self, message: str) -> str:
        try:
            encrypted_values = [str(ord(char) + self._offset(i)) for i, char in enumerate(message)]
            joined_string = self.delimiter.join(encrypted_values)
            encoded_b64 = __import__("base64").b64encode(joined_string.encode("utf-8")).decode("utf-8")
            return encoded_b64.rstrip("=")
        except Exception as e:
            raise Exception(f"Encryption failed for 'bytes' method: {e}")

    def encrypt_shift(self, text: str) -> str:
        encoded_hex = [hex(ord(text[i]) + ord(self.key[i % len(self.key)])) for i in range(len(text))]
        return self.delimiter.join(encoded_hex)

    def save(self, filename: str, code: str):
        encrypted_code = self.encrypt(code)
        if encrypted_code is None:
            raise ValueError("Encryption failed, cannot save.")
        result = f"exec(__import__('nsdev').CipherHandler(method='{self.method}', key={repr(self.key)}).decrypt('{encrypted_code}'))"
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
            self.key = self._normalize_key(key)
            if not self.key:
                raise ValueError("Key cannot be empty.")
        except Exception as e:
            raise Exception(f"Initialization failed: {e}")

    def _normalize_key(self, key) -> str:
        try:
            if isinstance(key, list):
                return "".join(map(str, key))
            return str(key)
        except Exception as e:
            raise Exception(f"Key normalization failed: {e}")

    def _offset(self, index: int) -> int:
        try:
            key_char_code = ord(self.key[index % len(self.key)])
            return len(self.key) * (index + 1) + key_char_code
        except Exception as e:
            raise Exception(f"Offset calculation failed at index {index}: {e}")

    def encrypt(self, message: str) -> list[int]:
        try:
            return [int(ord(char) + self._offset(i)) for i, char in enumerate(message)]
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")

    def decrypt(self, encrypted: list[int]) -> str:
        try:
            return "".join(chr(int(code) - self._offset(i)) for i, code in enumerate(encrypted))
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")

    def save_data(self, filename: str, code: str):
        try:
            encrypted_code = self.encrypt(code)
            result = f"exec(__import__('nsdev').AsciiManager({repr(self.no_format_key)}).decrypt({encrypted_code}))"
            with open(filename, "w") as file:
                file.write(result)
                print(f"{self.GREEN}Kode berhasil disimpan ke file {filename}{self.RESET}")
        except Exception as e:
            raise Exception(f"Failed to save data to {filename}: {e}")
