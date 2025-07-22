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
        self.os = __import__("os")
        self.stat = __import__("stat")
        self.json = __import__("json")
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.subprocess = __import__("subprocess")

        self.storage_type = options.get("storage_type", "local")
        self.file_name = options.get("file_name", "database")
        self.binary_keys = options.get("binary_keys", "default_db_key_12345")
        self.method_encrypt = options.get("method_encrypt", "bytes")

        self.cipher = __import__("nsdev").encrypt.CipherHandler(key=self.binary_keys, method=self.method_encrypt)

        self.auto_backup = options.get("auto_backup", False)
        self.backup_bot_token = options.get("backup_bot_token")
        self.backup_chat_id = options.get("backup_chat_id")
        self.backup_interval_hours = options.get("backup_interval_hours", 24)

        if self.storage_type == "mongo":
            self.pymongo = __import__("pymongo")
            self.mongo_url = options.get("mongo_url")
            if not self.mongo_url:
                raise ValueError("mongo_url is required for MongoDB storage")
            self.client = self.pymongo.MongoClient(self.mongo_url)
            self.data = self.client[self.file_name]

        elif self.storage_type == "sqlite":
            self.db_file = f"{self.file_name}.db"
            self.conn = __import__("sqlite3").connect(self.db_file, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self._initialize_sqlite()

        else:
            self.data_file = f"{self.file_name}.json"
            self._initialize_files()

        if self.auto_backup and self.storage_type in ["local", "sqlite"]:
            if not self.backup_bot_token or not self.backup_chat_id:
                self.cipher.log.print(
                    f"{self.cipher.log.YELLOW}[BACKUP] Auto backup diaktifkan tapi 'backup_bot_token' atau 'backup_chat_id' tidak disetel. Backup dinonaktifkan."
                )
            else:
                self._start_backup_thread()

    def _start_backup_thread(self):
        try:
            self.threading = __import__("threading")
            backup_thread = self.threading.Thread(target=self._backup_looper, daemon=True)
            backup_thread.start()
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal memulai thread backup: {e}")

    def _backup_looper(self):
        self.time = __import__("time")
        interval_seconds = self.backup_interval_hours * 3600
        self.cipher.log.print(
            f"{self.cipher.log.GREEN}[BACKUP] akan dijalankan dalam {self.backup_interval_hours} jam sekali."
        )

        while True:
            self.time.sleep(interval_seconds)
            try:
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] Memulai proses backup...")
                self._perform_backup()
            except Exception as e:
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Terjadi error pada loop backup: {e}")

    def _perform_backup(self):
        source_path = None
        if self.storage_type == "local":
            source_path = self.data_file
        elif self.storage_type == "sqlite":
            source_path = self.db_file

        if not source_path or not self.os.path.exists(source_path):
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[BACKUP] File database '{source_path}' tidak ditemukan. Backup dilewati."
            )
            return

        zip_path = None
        try:
            self.zipfile = __import__("zipfile")

            timestamp = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d_%H-%M-%S")
            zip_filename = f"{self.file_name}_backup_{timestamp}.zip"
            zip_path = zip_filename

            with self.zipfile.ZipFile(zip_path, "w", self.zipfile.ZIP_DEFLATED) as zf:
                zf.write(source_path, self.os.path.basename(source_path))

            self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] File '{zip_path}' berhasil dibuat.")

            caption = (
                f"Backup otomatis untuk `{self.file_name}`\n"
                f"Tipe: `{self.storage_type}`\n"
                f"Waktu: `{timestamp} WIB`"
            )

            self._send_zip_to_telegram(zip_path, caption)

        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Proses backup gagal: {e}")
        finally:
            if zip_path and self.os.path.exists(zip_path):
                self.os.remove(zip_path)
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] File '{zip_path}' telah dihapus.")

    def _send_zip_to_telegram(self, file_path, caption):
        try:
            self.requests = __import__("requests")
            url = f"https://api.telegram.org/bot{self.backup_bot_token}/sendDocument"

            with open(file_path, "rb") as doc:
                files = {"document": doc}
                params = {"chat_id": self.backup_chat_id, "caption": caption, "parse_mode": "Markdown"}
                response = self.requests.post(url, params=params, files=files, timeout=60)

            response_data = response.json()
            if response.status_code == 200 and response_data.get("ok"):
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] berhasil dikirim ke Telegram.")
            else:
                error_desc = response_data.get("description", "Unknown error")
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal mengirim ke Telegram: {error_desc}")

        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] Gagal mengirim file ke Telegram: {e}")

    def _initialize_files(self):
        if not self.os.path.exists(self.data_file):
            self._save_data({"vars": {}, "bots": []})

    def _load_data(self):
        try:
            with open(self.data_file, "r") as f:
                content = f.read()
                return self.json.loads(content) if content.strip() else {"vars": {}, "bots": []}
        except (self.json.JSONDecodeError, FileNotFoundError):
            return {"vars": {}, "bots": []}

    def _save_data(self, data):
        with open(self.data_file, "w") as f:
            self.json.dump(data, f, indent=4)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _initialize_sqlite(self):
        try:
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vars (
                    user_id TEXT PRIMARY KEY,
                    data TEXT
                )
            """
            )
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bots (
                    user_id TEXT PRIMARY KEY,
                    api_id TEXT,
                    api_hash TEXT,
                    bot_token TEXT,
                    session_string TEXT
                )
            """
            )
            self.conn.commit()
            self._set_permissions()
        except Exception as e:
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Inisialisasi DB gagal: {self.cipher.log.RED}{e}"
            )

    def _set_permissions(self):
        try:
            self.os.chmod(
                self.db_file,
                self.stat.S_IRUSR
                | self.stat.S_IWUSR
                | self.stat.S_IRGRP
                | self.stat.S_IROTH
                | self.stat.S_IWGRP
                | self.stat.S_IWOTH,
            )
            self.cipher.log.print(
                f"{self.cipher.log.GREEN}[SQLite] {self.cipher.log.CYAN}Permissions set: {self.cipher.log.BLUE}{self.db_file}"
            )
        except Exception as e:
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Set permissions gagal: {self.cipher.log.RED}{e}"
            )

    def close(self):
        if self.storage_type == "sqlite" and hasattr(self, "conn") and self.conn:
            try:
                self.conn.commit()
                self.conn.close()
                self.cipher.log.print(f"{self.cipher.log.GREEN}[SQLite] Koneksi ditutup")
                self.conn = None
            except Exception as e:
                self.cipher.log.print(
                    f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Gagal menutup koneksi: {self.cipher.log.RED}{e}"
                )

    def _sqlite_get_vars(self, user_id):
        self.cursor.execute("SELECT data FROM vars WHERE user_id = ?", (str(user_id),))
        row = self.cursor.fetchone()
        if row and row[0]:
            return self.json.loads(row[0])
        return {"vars": {str(user_id): {}}}

    def _sqlite_set_vars(self, user_id, data):
        try:
            self.cursor.execute(
                "INSERT OR REPLACE INTO vars (user_id, data) VALUES (?, ?)",
                (str(user_id), self.json.dumps(data)),
            )
            self.conn.commit()
        except Exception as e:
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Simpan vars gagal: {self.cipher.log.RED}{e}"
            )

    def _sqlite_remove_vars(self, user_id):
        self.cursor.execute("DELETE FROM vars WHERE user_id = ?", (str(user_id),))
        self.conn.commit()

    def _sqlite_get_bots(self):
        self.cursor.execute("SELECT user_id, api_id, api_hash, bot_token, session_string FROM bots")
        return self.cursor.fetchall()

    def _sqlite_set_bot(self, user_id, encrypted_data):
        try:
            self.cursor.execute(
                """
                INSERT OR REPLACE INTO bots (user_id, api_id, api_hash, bot_token, session_string)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    str(user_id),
                    encrypted_data["api_id"],
                    encrypted_data["api_hash"],
                    encrypted_data.get("bot_token"),
                    encrypted_data.get("session_string"),
                ),
            )
            self.conn.commit()
        except Exception as e:
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Simpan bot gagal: {self.cipher.log.RED}{e}"
            )

    def _sqlite_remove_bot(self, user_id):
        try:
            self.cursor.execute("DELETE FROM bots WHERE user_id = ?", (str(user_id),))
            self.conn.commit()
        except Exception as e:
            self.cipher.log.print(
                f"{self.cipher.log.YELLOW}[SQLite] {self.cipher.log.CYAN}Hapus bot gagal: {self.cipher.log.RED}{e}"
            )

    def _mongo_get_vars(self, user_id):
        result = self.data.vars.find_one({"_id": str(user_id)})
        return result if result else {}

    def _mongo_set_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one(
            {"_id": str(user_id)},
            {"$set": {f"{var_key}.{query_name}": encrypted_value}},
            upsert=True,
        )

    def _mongo_push_list_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one(
            {"_id": str(user_id)},
            {"$push": {f"{var_key}.{query_name}": encrypted_value}},
            upsert=True,
        )

    def _mongo_pull_list_vars(self, user_id, var_key, query_name, encrypted_value):
        self.data.vars.update_one({"_id": str(user_id)}, {"$pull": {f"{var_key}.{query_name}": encrypted_value}})

    def _mongo_unset_vars(self, user_id, var_key):
        self.data.vars.update_one({"_id": str(user_id)}, {"$unset": {var_key: ""}})

    def _mongo_remove_var(self, user_id, var_key, query_name):
        self.data.vars.update_one({"_id": str(user_id)}, {"$unset": {f"{var_key}.{query_name}": ""}})

    def _mongo_save_bot(self, user_id, encrypted_data):
        self.data.bot.update_one({"user_id": str(user_id)}, {"$set": encrypted_data}, upsert=True)

    def _mongo_remove_bot(self, user_id):
        self.data.bot.delete_one({"user_id": str(user_id)})

    def setVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        encrypted_value = self.cipher.encrypt(str(value))
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
            result = self._mongo_get_vars(user_id_str)
            encrypted_value = result.get(var_key, {}).get(query_name)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            encrypted_value = data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
        else:
            encrypted_value = self._load_data().get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)

        return self.cipher.decrypt(encrypted_value) if encrypted_value else None

    def removeVars(self, user_id, query_name, var_key="variabel"):
        user_id_str = str(user_id)
        if self.storage_type == "mongo":
            self._mongo_remove_var(user_id_str, var_key, query_name)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            user_vars = data.get("vars", {}).get(user_id_str, {}).get(var_key)
            if user_vars and query_name in user_vars:
                del user_vars[query_name]
                self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            user_vars = data.get("vars", {}).get(user_id_str, {}).get(var_key)
            if user_vars and query_name in user_vars:
                del user_vars[query_name]
                self._save_data(data)

    def setListVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        value_to_encrypt = self.json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(value_to_encrypt)

        if self.storage_type == "mongo":
            self._mongo_push_list_vars(user_id_str, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            user_data = data["vars"].setdefault(user_id_str, {}).setdefault(var_key, {})
            user_list = user_data.setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            user_data = data["vars"].setdefault(user_id_str, {}).setdefault(var_key, {})
            user_list = user_data.setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._save_data(data)

    def getListVars(self, user_id, query_name, var_key="variabel"):
        user_id_str = str(user_id)
        encrypted_values = []
        if self.storage_type == "mongo":
            result = self._mongo_get_vars(user_id_str)
            encrypted_values = result.get(var_key, {}).get(query_name, [])
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            encrypted_values = data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name, [])
        else:
            encrypted_values = (
                self._load_data().get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name, [])
            )

        decrypted_list = []
        for value in encrypted_values:
            decrypted_str = self.cipher.decrypt(value)
            try:
                decrypted_list.append(self.json.loads(decrypted_str))
            except (self.json.JSONDecodeError, TypeError):
                decrypted_list.append(decrypted_str)
        return decrypted_list

    def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        user_id_str = str(user_id)
        value_to_encrypt = self.json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(value_to_encrypt)

        if self.storage_type == "mongo":
            self._mongo_pull_list_vars(user_id_str, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            user_list = data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
            if user_list and encrypted_value in user_list:
                user_list.remove(encrypted_value)
                self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            user_list = data.get("vars", {}).get(user_id_str, {}).get(var_key, {}).get(query_name)
            if user_list and encrypted_value in user_list:
                user_list.remove(encrypted_value)
                self._save_data(data)

    def removeAllVars(self, user_id, var_key="variabel"):
        user_id_str = str(user_id)
        if self.storage_type == "mongo":
            self._mongo_unset_vars(user_id_str, var_key)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            if data.get("vars", {}).get(user_id_str):
                del data["vars"][user_id_str]
            self._sqlite_set_vars(user_id_str, data)
        else:
            data = self._load_data()
            if data.get("vars") and data["vars"].get(user_id_str):
                data["vars"].pop(user_id_str, None)
            self._save_data(data)

    def allVars(self, user_id, var_key="variabel", no_decrypt=False):
        user_id_str = str(user_id)
        encrypted_data = {}
        if self.storage_type == "mongo":
            result = self._mongo_get_vars(user_id_str)
            encrypted_data = result.get(var_key, {})
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id_str)
            encrypted_data = data.get("vars", {}).get(user_id_str, {}).get(var_key, {})
        else:
            encrypted_data = self._load_data().get("vars", {}).get(user_id_str, {}).get(var_key, {})

        if no_decrypt:
            return self.json.dumps(encrypted_data, indent=4)
        else:
            decrypted = {}
            for key, value in encrypted_data.items():
                if isinstance(value, list):
                    temp_list = []
                    for v in value:
                        decrypted_v_str = self.cipher.decrypt(v)
                        try:
                            temp_list.append(self.json.loads(decrypted_v_str))
                        except (self.json.JSONDecodeError, TypeError):
                            temp_list.append(decrypted_v_str)
                    decrypted[key] = temp_list
                elif isinstance(value, str):
                    decrypted[key] = self.cipher.decrypt(value)
                else:
                    decrypted[key] = value

            return self.json.dumps(decrypted, indent=4)

    def setExp(self, user_id, exp=30):
        user_id_str = str(user_id)
        have_exp = self.getVars(user_id_str, "EXPIRED_DATE")
        if not have_exp:
            now = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
        else:
            now = self.datetime.datetime.strptime(have_exp, "%Y-%m-%d %H:%M:%S").astimezone(
                self.zoneinfo.ZoneInfo("Asia/Jakarta")
            )
        expire_date = now + self.datetime.timedelta(days=exp)
        self.setVars(user_id_str, "EXPIRED_DATE", expire_date.strftime("%Y-%m-%d %H:%M:%S"))

    def getExp(self, user_id):
        user_id_str = str(user_id)
        expired_date = self.getVars(user_id_str, "EXPIRED_DATE")
        if expired_date:
            exp_datetime = self.datetime.datetime.strptime(expired_date, "%Y-%m-%d %H:%M:%S").astimezone(
                self.zoneinfo.ZoneInfo("Asia/Jakarta")
            )
            return exp_datetime.strftime("%d-%m-%Y")
        return None

    def daysLeft(self, user_id):
        user_id_str = str(user_id)
        user_exp = self.getExp(user_id_str)
        today = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
        if user_exp:
            exp_datetime = self.datetime.datetime.strptime(user_exp, "%d-%m-%Y").astimezone(
                self.zoneinfo.ZoneInfo("Asia/Jakarta")
            )
            return (exp_datetime - today).days
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
            self._mongo_save_bot(user_id_str, encrypted_data)
        elif self.storage_type == "sqlite":
            self._sqlite_set_bot(user_id_str, encrypted_data)
        else:
            data = self._load_data()
            bot_exists = False
            for bot in data["bots"]:
                if bot["user_id"] == user_id_str:
                    bot.update(encrypted_data)
                    bot_exists = True
                    break
            if not bot_exists:
                entry = {"user_id": user_id_str, **encrypted_data}
                data["bots"].append(entry)
            self._save_data(data)

    def getBots(self, is_token=False):
        field = "bot_token" if is_token else "session_string"
        bots_data = []

        if self.storage_type == "mongo":
            raw_bots = self.data.bot.find({field: {"$exists": True}})
        elif self.storage_type == "sqlite":
            rows = self._sqlite_get_bots()
            raw_bots = [
                {"user_id": row[0], "api_id": row[1], "api_hash": row[2], "bot_token": row[3], "session_string": row[4]}
                for row in rows
                if (row[3] if is_token else row[4])
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
            self._mongo_remove_bot(user_id_str)
        elif self.storage_type == "sqlite":
            self._sqlite_remove_bot(user_id_str)
        else:
            data = self._load_data()
            data["bots"] = [bot for bot in data["bots"] if bot.get("user_id") != user_id_str]
            self._save_data(data)
