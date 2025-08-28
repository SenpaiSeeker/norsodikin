import datetime
import json
import os
import sqlite3
import stat
import threading
import time
import zipfile
import zoneinfo

import requests

from ..code.encrypt import CipherHandler


class DataBase:
    def __init__(self, **options):
        """
        :param options:
            - storage_type (str): 'local' (default), 'mongo', atau 'sqlite'.
            - file_name (str): Nama file untuk database lokal/SQLite (default: 'database').
            - binary_keys (str | int): Kunci enkripsi untuk CipherHandler.
            - method_encrypt (str): Metode enkripsi untuk CipherHandler (default: 'bytes').
            - mongo_url (str): URL MongoDB (wajib jika storage_type='mongo').
            - auto_backup (bool): Mengaktifkan backup otomatis ke Telegram (default: False).
            - backup_bot_token (str): Token Bot Telegram untuk mengirim backup.
            - backup_chat_id (str|int): Chat ID tujuan untuk backup Telegram.
            - backup_interval_hours (int): Interval backup dalam jam (default: 24).
        """
        self.storage_type = options.get("storage_type", "local")
        self.file_name = options.get("file_name", "database")
        self.keys_encrypt = options.get("keys_encrypt", "default_db_key_12345")
        self.method_encrypt = options.get("method_encrypt", "bytes")
        self.cipher = CipherHandler(key=self.keys_encrypt, method=self.method_encrypt)
        self.auto_backup = options.get("auto_backup", False)
        self.backup_bot_token = options.get("backup_bot_token")
        self.backup_chat_id = options.get("backup_chat_id")
        self.backup_interval_hours = options.get("backup_interval_hours", 24)
        if self.storage_type == "mongo":
            import pymongo

            self.mongo_url = options.get("mongo_url")
            if not self.mongo_url:
                raise ValueError("mongo_url is required for MongoDB storage")
            self.client = pymongo.MongoClient(self.mongo_url)
            self.data = self.client[self.file_name]
        elif self.storage_type == "sqlite":
            self.db_file = f"{self.file_name}.db"
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._initialize_sqlite()
        else:
            self.data_file = f"{self.file_name}.json"
            self._initialize_files()
        if self.auto_backup and self.storage_type in ["local", "sqlite"]:
            if not self.backup_bot_token or not self.backup_chat_id:
                self.cipher.log.print(
                    f"{self.cipher.log.YELLOW}[BACKUP] Auto backup disabled due to missing credentials."
                )
            else:
                self._start_backup_thread()

    def _start_backup_thread(self):
        try:
            backup_thread = threading.Thread(target=self._backup_looper, daemon=True)
            backup_thread.start()
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal memulai thread backup: {e}")

    def _backup_looper(self):
        interval_seconds = self.backup_interval_hours * 3600
        self.cipher.log.print(
            f"{self.cipher.log.GREEN}[BACKUP] akan dijalankan setiap {self.backup_interval_hours} jam."
        )
        while True:
            time.sleep(interval_seconds)
            try:
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] Memulai proses backup...")
                self._perform_backup()
            except Exception as e:
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Error pada loop backup: {e}")

    def _perform_backup(self):
        source_path = self.data_file if self.storage_type == "local" else self.db_file
        if not source_path or not os.path.exists(source_path):
            self.cipher.log.print(f"{self.cipher.log.YELLOW}[BACKUP] File database tidak ditemukan. Backup dilewati.")
            return
        zip_path = None
        try:
            timestamp = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d_%H-%M-%S")
            zip_filename = f"{self.file_name}_backup_{timestamp}.zip"
            zip_path = zip_filename
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(source_path, os.path.basename(source_path))
            self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] File '{zip_path}' berhasil dibuat.")
            caption = f"Backup otomatis untuk `{self.file_name}`\nTipe: `{self.storage_type}`\nWaktu: `{timestamp} WIB`"
            self._send_zip_to_telegram(zip_path, caption)
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Proses backup gagal: {e}")
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] File '{zip_path}' telah dihapus.")

    def _send_zip_to_telegram(self, file_path, caption):
        try:
            url = f"https://api.telegram.org/bot{self.backup_bot_token}/sendDocument"
            with open(file_path, "rb") as doc:
                files = {"document": doc}
                params = {"chat_id": self.backup_chat_id, "caption": caption, "parse_mode": "Markdown"}
                response = requests.post(url, params=params, files=files, timeout=60)
            response_data = response.json()
            if response.status_code == 200 and response_data.get("ok"):
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] berhasil dikirim ke Telegram.")
            else:
                error_desc = response_data.get("description", "Unknown error")
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal mengirim ke Telegram: {error_desc}")
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal mengirim file ke Telegram: {e}")

    def _initialize_files(self):
        if not os.path.exists(self.data_file):
            self._save_data({"vars": {}, "bots": []})

    def _load_data(self):
        try:
            with open(self.data_file, "r") as f:
                content = f.read()
                return json.loads(content) if content.strip() else {"vars": {}, "bots": []}
        except (json.JSONDecodeError, FileNotFoundError):
            return {"vars": {}, "bots": []}

    def _save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _initialize_sqlite(self):
        try:
            self.cursor.execute("CREATE TABLE IF NOT EXISTS vars (user_id TEXT PRIMARY KEY, data TEXT)")
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bots (
                    user_id TEXT PRIMARY KEY, api_id TEXT, api_hash TEXT,
                    bot_token TEXT, session_string TEXT
                )
            """
            )
            self.conn.commit()
            self._set_permissions()
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[SQLite] Inisialisasi DB gagal: {e}")

    def _set_permissions(self):
        try:
            os.chmod(
                self.db_file, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH
            )
            self.cipher.log.print(f"{self.cipher.log.GREEN}[SQLite] Permissions set: {self.db_file}")
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[SQLite] Set permissions gagal: {e}")

    def close(self):
        if self.storage_type == "sqlite" and hasattr(self, "conn") and self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                self.conn = None
            except Exception as e:
                self.cipher.log.print(f"{self.cipher.log.RED}[SQLite] Gagal menutup koneksi: {e}")

    def _sqlite_get_vars(self, user_id):
        self.cursor.execute("SELECT data FROM vars WHERE user_id = ?", (str(user_id),))
        row = self.cursor.fetchone()
        return json.loads(row[0]) if row and row[0] else {"vars": {str(user_id): {}}}

    def _sqlite_set_vars(self, user_id, data):
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO vars (user_id, data) VALUES (?, ?)", (str(user_id), json.dumps(data))
            )
            self.conn.commit()
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[SQLite] Simpan vars gagal: {e}")

    def _mongo_get_vars(self, user_id):
        return self.data.vars.find_one({"_id": str(user_id)}) or {}

    def _mongo_set_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one(
            {"_id": str(user_id)}, {"$set": {f"{var_key}.{query_name}": encrypted_value}}, upsert=True
        )

    def _mongo_push_list_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one(
            {"_id": str(user_id)}, {"$push": {f"{var_key}.{query_name}": encrypted_value}}, upsert=True
        )

    def _mongo_pull_list_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one({"_id": str(user_id)}, {"$pull": {f"{var_key}.{query_name}": encrypted_value}})

    def setVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        value_to_encrypt = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(value_to_encrypt)
        if self.storage_type == "mongo":
            self._mongo_set_vars(user_id_str, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            user_data = data["vars"].setdefault(user_id_str, {})
            user_data.setdefault(var_key, {})[query_name] = encrypted_value
            self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            user_data = data["vars"].setdefault(user_id_str, {})
            user_data.setdefault(var_key, {})[query_name] = encrypted_value
            self._save_data(data)

    def getVars(self, user_id, query_name, var_key="variabel"):
        user_id_str = str(user_id)
        encrypted_value = None
        if self.storage_type == "mongo":
            encrypted_value = self._mongo_get_vars(user_id_str).get(var_key, {}).get(query_name)
        elif self.storage_type == "sqlite":
            encrypted_value = (
                self._sqlite_get_vars(user_id_str).get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
            )
        else:
            encrypted_value = self._load_data().get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
        if not encrypted_value:
            return None
        decrypted_str = self.cipher.decrypt(encrypted_value)
        try:
            return json.loads(decrypted_str)
        except (json.JSONDecodeError, TypeError):
            return decrypted_str

    def removeVars(self, user_id, query_name, var_key="variabel"):
        user_id_str = str(user_id)
        if self.storage_type == "mongo":
            self.data.vars.update_one({"_id": user_id_str}, {"$unset": {f"{var_key}.{query_name}": ""}})
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            if data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).pop(query_name, None):
                self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            if data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).pop(query_name, None):
                self._save_data(data)

    def setListVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        value_to_encrypt = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(value_to_encrypt)
        if self.storage_type == "mongo":
            self._mongo_push_list_vars(user_id_str, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            user_list = data["vars"].setdefault(user_id_str, {}).setdefault(var_key, {}).setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            user_list = data["vars"].setdefault(user_id_str, {}).setdefault(var_key, {}).setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._save_data(data)

    def getListVars(self, user_id, query_name, var_key="variabel"):
        user_id_str = str(user_id)
        encrypted_values = []
        if self.storage_type == "mongo":
            encrypted_values = self._mongo_get_vars(user_id_str).get(var_key, {}).get(query_name, [])
        elif self.storage_type == "sqlite":
            encrypted_values = (
                self._sqlite_get_vars(user_id_str)
                .get("vars", {})
                .get(user_id_str, {})
                .get(var_key, {})
                .get(query_name, [])
            )
        else:
            encrypted_values = (
                self._load_data().get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name, [])
            )
        decrypted_list = []
        for value in encrypted_values:
            decrypted_str = self.cipher.decrypt(value)
            try:
                decrypted_list.append(json.loads(decrypted_str))
            except (json.JSONDecodeError, TypeError):
                decrypted_list.append(decrypted_str)
        return decrypted_list

    def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        value_to_encrypt = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(value_to_encrypt)
        if self.storage_type == "mongo":
            self._mongo_pull_list_vars(user_id_str, var_key, query_name, encrypted_value)
        else:
            if self.storage_type == "sqlite":
                data = self._sqlite_get_vars(user_id_str)
            else:
                data = self._load_data()
            user_list = data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
            if user_list and encrypted_value in user_list:
                user_list.remove(encrypted_value)
                if self.storage_type == "sqlite":
                    self._sqlite_set_vars(user_id_str, data)
                else:
                    self._save_data(data)

    def setExp(self, user_id, exp=30):
        user_id_str = str(user_id)
        have_exp = self.getVars(user_id_str, "EXPIRED_DATE")
        now = datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Jakarta"))
        if have_exp:
            now = datetime.datetime.strptime(have_exp, "%Y-%m-%d %H:%M:%S").astimezone(
                zoneinfo.ZoneInfo("Asia/Jakarta")
            )
        expire_date = now + datetime.timedelta(days=exp)
        self.setVars(user_id_str, "EXPIRED_DATE", expire_date.strftime("%Y-%m-%d %H:%M:%S"))

    def daysLeft(self, user_id):
        user_id_str = str(user_id)
        expired_date = self.getVars(user_id_str, "EXPIRED_DATE")
        if expired_date:
            exp_datetime = datetime.datetime.strptime(expired_date, "%Y-%m-%d %H:%M:%S").astimezone(
                zoneinfo.ZoneInfo("Asia/Jakarta")
            )
            return (exp_datetime - datetime.datetime.now(zoneinfo.ZoneInfo("Asia/Jakarta"))).days
        return None

    def checkAndDeleteIfExpired(self, user_id):
        user_id_str = str(user_id)
        days_left = self.daysLeft(user_id_str)
        if days_left is not None and days_left < 0:
            self.removeAllVars(user_id_str)
            self.removeBot(user_id_str)
            return True
        return False

    def saveBot(self, user_id, api_id, api_hash, value, is_token=False):
        user_id_str = str(user_id)
        field = "bot_token" if is_token else "session_string"
        encrypted_data = {
            "api_id": self.cipher.encrypt(str(api_id)),
            "api_hash": self.cipher.encrypt(api_hash),
        }
        if value:
            encrypted_data[field] = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            self.data.bot.update_one({"user_id": user_id_str}, {"$set": encrypted_data}, upsert=True)
        elif self.storage_type == "sqlite":
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO bots (user_id, api_id, api_hash, bot_token, session_string)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_id_str,
                    encrypted_data["api_id"],
                    encrypted_data["api_hash"],
                    encrypted_data.get("bot_token"),
                    encrypted_data.get("session_string"),
                ),
            )
            self.conn.commit()
        else:
            data = self._load_data()
            bot_exists = False
            for bot in data["bots"]:
                if bot["user_id"] == user_id_str:
                    bot.update(encrypted_data)
                    bot_exists = True
                    break
            if not bot_exists:
                data["bots"].append({"user_id": user_id_str, **encrypted_data})
            self._save_data(data)

    def getBots(self, is_token=False):
        field = "bot_token" if is_token else "session_string"
        bots_data = []
        raw_bots = []
        if self.storage_type == "mongo":
            raw_bots = self.data.bot.find({field: {"$exists": True}})
        elif self.storage_type == "sqlite":
            self.cursor.execute("SELECT user_id, api_id, api_hash, bot_token, session_string FROM bots")
            rows = self.cursor.fetchall()
            raw_bots = [
                {"user_id": r[0], "api_id": r[1], "api_hash": r[2], "bot_token": r[3], "session_string": r[4]}
                for r in rows
                if (r[3] if is_token else r[4])
            ]
        else:
            raw_bots = [bot for bot in self._load_data().get("bots", []) if field in bot]
        for bot_data in raw_bots:
            try:
                decrypted_bot = {
                    "name": str(bot_data["user_id"]),
                    "api_id": int(self.cipher.decrypt(str(bot_data["api_id"]))),
                    "api_hash": self.cipher.decrypt(bot_data["api_hash"]),
                    field: self.cipher.decrypt(bot_data.get(field)),
                }
                bots_data.append(decrypted_bot)
            except (ValueError, TypeError):
                continue
        return bots_data

    def removeBot(self, user_id):
        user_id_str = str(user_id)
        if self.storage_type == "mongo":
            self.data.bot.delete_one({"user_id": user_id_str})
        elif self.storage_type == "sqlite":
            self.cursor.execute("DELETE FROM bots WHERE user_id = ?", (user_id_str,))
            self.conn.commit()
        else:
            data = self._load_data()
            data["bots"] = [bot for bot in data["bots"] if bot.get("user_id") != user_id_str]
            self._save_data(data)
