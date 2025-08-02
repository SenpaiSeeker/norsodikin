class CipherHandler:
    """
    Handler untuk enkripsi dan dekripsi menggunakan berbagai metode.

    :param options:
        - method (str): Metode enkripsi/dekripsi. Pilihan: 'shift', 'bytes', 'binary', Default: shift.
        - key (str | list | int | float): Kunci untuk proses enkripsi/dekripsi. Default: 'my_s3cr3t_k3y_@2024!'.
        - delimiter (str): Delimiter yang digunakan dalam pemisahan data terenkripsi. Default: '|'.
    """

    def __init__(self, **options):
        self.base64 = __import__("base64")
        self.binascii = __import__("binascii")
        self.json = __import__("json")

        self.method = options.get("method", "shift")
        self.key = self._normalize_key(options.get("key", "my_s3cr3t_k3y_@2024!"))
        self.numeric_key = self._get_numeric_key()
        self.delimiter = options.get("delimiter", "|")

        if not self.key:
            raise ValueError("Key cannot be empty.")

        self.log = __import__("nsdev").logger.LoggerHandler()

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

    def _base64_encode(self, data: str) -> str:
        encoded_bytes = self.base64.b64encode(data.encode("utf-8"))
        return encoded_bytes.decode("utf-8").rstrip("=")

    def _base64_decode(self, encoded_data: str) -> str:
        try:
            padding_needed = (4 - len(encoded_data) % 4) % 4
            padded_data = encoded_data + "=" * padding_needed
            decoded_bytes = self.base64.b64decode(padded_data)
            return decoded_bytes.decode("utf-8")
        except (self.binascii.Error, UnicodeDecodeError) as e:
            raise ValueError(f"Base64 decryption failed: {e}")

    def decrypt(self, encrypted_data: str, only_base64: bool = False):
        if only_base64:
            return self._base64_decode(encrypted_data)

        decrypted_string = ""
        if self.method == "bytes":
            decrypted_string = self.decrypt_bytes(encrypted_data)
        elif self.method == "binary":
            decrypted_string = self.decrypt_binary(encrypted_data)
        elif self.method == "shift":
            decrypted_string = self.decrypt_shift(encrypted_data)
        else:
            raise ValueError(f"Metode dekripsi '{self.method}' tidak dikenali.")

        try:
            return self.json.loads(decrypted_string)
        except (self.json.JSONDecodeError, TypeError):
            return decrypted_string

    def decrypt_binary(self, encrypted_bits: str) -> str:
        if not encrypted_bits or len(encrypted_bits) % 8 != 0:
            raise ValueError("Data biner yang dienkripsi tidak valid atau kosong.")
        decrypted_chars = [
            chr(int(encrypted_bits[i : i + 8], 2) ^ self.numeric_key % 256) for i in range(0, len(encrypted_bits), 8)
        ]
        return "".join(decrypted_chars)

    def decrypt_bytes(self, encrypted_data: str) -> str:
        try:
            encrypted_bytes = bytes.fromhex(encrypted_data)
            decrypted_bytes = self._xor_encrypt_decrypt(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            raise Exception(f"Decryption failed for 'bytes' method: {e}")

    def decrypt_shift(self, encoded_text: str) -> str:
        try:
            codes = encoded_text.split(self.delimiter)
            return "".join(chr(int(code, 16) - ord(self.key[i % len(self.key)])) for i, code in enumerate(codes))
        except (ValueError, TypeError) as error:
            raise ValueError(f"Error during shift decryption: {error}")

    def encrypt(self, data, only_base64: bool = False) -> str:
        if only_base64:
            return self._base64_encode(data)

        if not isinstance(data, str):
            message_to_encrypt = self.json.dumps(data, separators=(",", ":"))
        else:
            message_to_encrypt = data

        if self.method == "bytes":
            return self.encrypt_bytes(message_to_encrypt)
        elif self.method == "binary":
            return self.encrypt_binary(message_to_encrypt)
        elif self.method == "shift":
            return self.encrypt_shift(message_to_encrypt)
        else:
            raise ValueError(f"Metode enkripsi '{self.method}' tidak dikenali.")

    def encrypt_binary(self, plaintext: str) -> str:
        xor_key = self.numeric_key % 256
        encrypted_bits = "".join(format(ord(char) ^ xor_key, "08b") for char in plaintext)
        return encrypted_bits

    def encrypt_bytes(self, message: str) -> str:
        try:
            encrypted_bytes = self._xor_encrypt_decrypt(message.encode("utf-8"))
            return encrypted_bytes.hex()
        except Exception as e:
            raise Exception(f"Encryption failed for 'bytes' method: {e}")

    def encrypt_shift(self, text: str) -> str:
        encoded_hex = [hex(ord(text[i]) + ord(self.key[i % len(self.key)])) for i in range(len(text))]
        return self.delimiter.join(encoded_hex)

    def save(self, filename: str, code: str, key_by_config: str = None):
        encrypted_code = self.encrypt(code)
        if encrypted_code is None:
            raise ValueError("Encryption failed, cannot save.")

        to_hex = lambda s: s.encode("utf-8").hex()
        hex_map = {
            "n": to_hex("nsdev"),
            "C": to_hex("CipherHandler"),
            "b": to_hex("builtins"),
            "t": to_hex("types"),
            "g": to_hex("globals"),
            "i": to_hex("__import__"),
            "a": to_hex("getattr"),
            "c": to_hex("compile"),
            "f": to_hex("FunctionType"),
            "M": to_hex(self.method),
        }

        if key_by_config is not None:
            key_for_output = key_by_config
        else:
            key_for_output = repr(self.key)

        result = (
            f"(lambda d, k, h, x: "
            f"(lambda b, i, g, c, t, f: "
            f"f(c(g(g(i(x(h['n'])), x(h['C']))(**{{'method': x(h['M']), 'key': k}}), 'decrypt')(d), '<string>', 'exec'), t())()"
            f")"
            f"(__import__(x(h['b'])), "
            f"lambda n: __import__(x(h['b'])).__dict__[x(h['i'])](n), "
            f"lambda o, n: __import__(x(h['b'])).__dict__[x(h['a'])](o, n), "
            f"lambda *a: __import__(x(h['b'])).__dict__[x(h['c'])](*a), "
            f"lambda: __import__(x(h['b'])).__dict__[x(h['g'])](), "
            f"lambda *a: __import__(x(h['b'])).__dict__[x(h['a'])](__import__(x(h['t'])), x(h['f']))(*a))"
            f")('{encrypted_code}', {key_for_output}, {hex_map}, lambda s: bytes.fromhex(s).decode('utf-8'))"
        )

        try:
            with open(filename, "w") as file:
                file.write(result)
            self.log.info(f"Kode berhasil disimpan ke file {filename}")
        except Exception as e:
            raise IOError(f"Saving file failed: {e}")


class AsciiManager(__import__("nsdev").AnsiColors):
    def __init__(self, key):
        super().__init__()
        self.json = __import__("json")
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

    def encrypt(self, data) -> list[int]:
        try:
            if not isinstance(data, str):
                message = self.json.dumps(data, separators=(",", ":"))
            else:
                message = data
            return [int(ord(char) + self._offset(i)) for i, char in enumerate(message)]
        except Exception as e:
            raise Exception(f"Encryption failed: {e}")

    def decrypt(self, encrypted: list[int]):
        try:
            decrypted_string = "".join(chr(int(code) - self._offset(i)) for i, code in enumerate(encrypted))
            try:
                return self.json.loads(decrypted_string)
            except (self.json.JSONDecodeError, TypeError):
                return decrypted_string
        except Exception as e:
            raise Exception(f"Decryption failed: {e}")

    def save_data(self, filename: str, code: str, key_by_config: str = None):
        try:
            encrypted_code = self.encrypt(code)

            to_hex = lambda s: s.encode("utf-8").hex()
            hex_map = {
                "n": to_hex("nsdev"),
                "A": to_hex("AsciiManager"),
                "b": to_hex("builtins"),
                "t": to_hex("types"),
                "g": to_hex("globals"),
                "i": to_hex("__import__"),
                "a": to_hex("getattr"),
                "c": to_hex("compile"),
                "f": to_hex("FunctionType"),
            }

            if key_by_config is not None:
                key_for_output = key_by_config
            else:
                key_for_output = repr(self.no_format_key)

            result = (
                f"(lambda d, k, h, x: "
                f"(lambda b, i, g, c, t, f: "
                f"f(c(g(g(i(x(h['n'])), x(h['A']))(k), 'decrypt')(d), '<string>', 'exec'), t())()"
                f")"
                f"(__import__(x(h['b'])), "
                f"lambda n: __import__(x(h['b'])).__dict__[x(h['i'])](n), "
                f"lambda o, n: __import__(x(h['b'])).__dict__[x(h['a'])](o, n), "
                f"lambda *a: __import__(x(h['b'])).__dict__[x(h['c'])](*a), "
                f"lambda: __import__(x(h['b'])).__dict__[x(h['g'])](), "
                f"lambda *a: __import__(x(h['b'])).__dict__[x(h['a'])](__import__(x(h['t'])), x(h['f']))(*a))"
                f")({str(encrypted_code)}, {key_for_output}, {hex_map}, lambda s: bytes.fromhex(s).decode('utf-8'))"
            )

            with open(filename, "w") as file:
                file.write(result)
                print(f"{self.GREEN}Kode berhasil disimpan ke file {filename}{self.RESET}")
        except Exception as e:
            raise Exception(f"Failed to save data to {filename}: {e}")
