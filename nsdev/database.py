class DataBase:
    def __init__(self, **options):
        """
        :param options:
            - storage_type (str): 'local' (default), 'mongo', atau 'sqlite'.
            - file_name (str): Nama file untuk database lokal/SQLite (default: 'database').
            - binary_keys (int): Kunci enkripsi untuk CipherHandler (default: 14151819154911914).
            - method_encrypt (str): Metode enkripsi untuk CipherHandler (default: 'bytes').
            - mongo_url (str): URL MongoDB (wajib jika storage_type='mongo').
        """
        self.os = __import__("os")
        self.json = __import__("json")
        self.datetime = __import__("datetime")
        self.zoneinfo = __import__("zoneinfo")
        self.subprocess = __import__("subprocess")
        self.storage_type = options.get("storage_type", "local")
        self.file_name = options.get("file_name", "database")
        self.binary_keys = options.get("binary_keys", 14151819154911914)
        self.method_encrypt = options.get("method_encrypt", "bytes")

        if self.storage_type == "mongo":
            self.pymongo = __import__("pymongo")
            self.mongo_url = options.get("mongo_url")
            if not self.mongo_url:
                raise ValueError("mongo_url is required for MongoDB storage")
            self.client = self.pymongo.MongoClient(self.mongo_url)
            self.data = self.client[self.file_name]
        elif self.storage_type == "sqlite":
            self.db_file = f"{self.file_name}.db"
            self.conn = __import__("sqlite3").connect(self.db_file)
            self.cursor = self.conn.cursor()
            self._initialize_sqlite()
        else:
            self.data_file = f"{self.file_name}.json"
            self._initialize_files()

        self.cipher = __import__("nsdev").encrypt.CipherHandler(key=self.binary_keys, method=self.method_encrypt)

    # File-based methods
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

    # SQLite-specific methods
    def _initialize_sqlite(self):
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

    def _sqlite_get_vars(self, user_id):
        self.cursor.execute("SELECT data FROM vars WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        return self.json.loads(row[0]) if row and row[0] else {"vars": {}}

    def _sqlite_set_vars(self, user_id, data):
        self.cursor.execute("INSERT OR REPLACE INTO vars (user_id, data) VALUES (?, ?)", (user_id, self.json.dumps(data)))
        self.conn.commit()

    def _sqlite_remove_vars(self, user_id):
        self.cursor.execute("DELETE FROM vars WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def _sqlite_get_bots(self):
        self.cursor.execute("SELECT user_id, api_id, api_hash, bot_token, session_string FROM bots")
        return self.cursor.fetchall()

    def _sqlite_set_bot(self, user_id, encrypted_data):
        self.cursor.execute(
            """
            INSERT OR REPLACE INTO bots (user_id, api_id, api_hash, bot_token, session_string)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, encrypted_data["api_id"], encrypted_data["api_hash"], encrypted_data.get("bot_token"), encrypted_data.get("session_string")),
        )
        self.conn.commit()

    def _sqlite_remove_bot(self, user_id):
        self.cursor.execute("DELETE FROM bots WHERE user_id = ?", (user_id,))
        self.conn.commit()

    # MongoDB-specific methods
    def _mongo_get_vars(self, user_id):
        result = self.data.vars.find_one({"_id": user_id})
        return result if result else {}

    def _mongo_set_vars(self, user_id, var_key, query_name, encrypted_value):
        update_data = {"$set": {f"{var_key}.{query_name}": encrypted_value}}
        self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)

    def _mongo_push_list_vars(self, user_id, var_key, query_name, encrypted_value):
        update_data = {"$push": {f"{var_key}.{query_name}": encrypted_value}}
        self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)

    def _mongo_pull_list_vars(self, user_id, var_key, query_name, encrypted_value):
        update_data = {"$pull": {f"{var_key}.{query_name}": encrypted_value}}
        self.data.vars.update_one({"_id": user_id}, update_data)

    def _mongo_unset_vars(self, user_id, var_key):
        update_data = {"$unset": {var_key: ""}}
        self.data.vars.update_one({"_id": user_id}, update_data)

    def _mongo_save_bot(self, user_id, encrypted_data):
        filter_query = {"user_id": user_id}
        update_data = {"$set": encrypted_data}
        self.data.bot.update_one(filter_query, update_data, upsert=True)

    def _mongo_remove_bot(self, user_id):
        self.data.bot.delete_one({"user_id": user_id})

    # General methods
    def setVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            self._mongo_set_vars(user_id, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            user_data = data["vars"].setdefault(str(user_id), {})
            user_data[var_key] = user_data.get(var_key, {})
            user_data[var_key][query_name] = encrypted_value
            self._sqlite_set_vars(user_id, data)
        else:
            data = self._load_data()
            user_data = data["vars"].setdefault(str(user_id), {})
            user_data[var_key] = user_data.get(var_key, {})
            user_data[var_key][query_name] = encrypted_value
            self._save_data(data)

    def getVars(self, user_id, query_name, var_key="variabel"):
        if self.storage_type == "mongo":
            result = self._mongo_get_vars(user_id)
            encrypted_value = result.get(var_key, {}).get(query_name, None)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            encrypted_value = data.get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name)
        else:
            encrypted_value = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name)
        return self.cipher.decrypt(encrypted_value) if encrypted_value else None

    def setListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            self._mongo_push_list_vars(user_id, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            user_data = data["vars"].setdefault(str(user_id), {})
            user_data[var_key] = user_data.get(var_key, {})
            user_list = user_data[var_key].setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._sqlite_set_vars(user_id, data)
        else:
            data = self._load_data()
            user_data = data["vars"].setdefault(str(user_id), {})
            user_data[var_key] = user_data.get(var_key, {})
            user_list = user_data[var_key].setdefault(query_name, [])
            if encrypted_value not in user_list:
                user_list.append(encrypted_value)
                self._save_data(data)

    def getListVars(self, user_id, query_name, var_key="variabel"):
        if self.storage_type == "mongo":
            result = self._mongo_get_vars(user_id)
            encrypted_values = result.get(var_key, {}).get(query_name, [])
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            encrypted_values = data.get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name, [])
        else:
            encrypted_values = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name, [])
        return [self.cipher.decrypt(value) for value in encrypted_values]

    def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            self._mongo_pull_list_vars(user_id, var_key, query_name, encrypted_value)
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            user_data = data.get("vars", {}).get(str(user_id), {}).get(var_key, {})
            if query_name in user_data and encrypted_value in user_data[query_name]:
                user_data[query_name].remove(encrypted_value)
                self._sqlite_set_vars(user_id, data)
        else:
            data = self._load_data()
            user_data = data.get("vars", {}).get(str(user_id), {}).get(var_key, {})
            if query_name in user_data and encrypted_value in user_data[query_name]:
                user_data[query_name].remove(encrypted_value)
                self._save_data(data)

    def removeAllVars(self, user_id, var_key="variabel"):
        if self.storage_type == "mongo":
            self._mongo_unset_vars(user_id, var_key)
        elif self.storage_type == "sqlite":
            self._sqlite_remove_vars(user_id)
        else:
            data = self._load_data()
            data["vars"].pop(str(user_id), None)
            self._save_data(data)

    def allVars(self, user_id, var_key="variabel"):
        if self.storage_type == "mongo":
            result = self._mongo_get_vars(user_id)
            encrypted_data = result.get(var_key, {}) if result else {}
        elif self.storage_type == "sqlite":
            data = self._sqlite_get_vars(user_id)
            encrypted_data = data.get("vars", {}).get(str(user_id), {}).get(var_key, {})
        else:
            encrypted_data = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {})
        decrypted = {
            key: ([self.cipher.decrypt(v) for v in value] if isinstance(value, list) else self.cipher.decrypt(value) if isinstance(value, str) else value)
            for key, value in encrypted_data.items()
        }
        return self.json.dumps(decrypted, indent=4)

    def setExp(self, user_id, exp=30):
        have_exp = self.getVars(user_id, "EXPIRED_DATE")
        if not have_exp:
            now = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
        else:
            now = self.datetime.datetime.strptime(have_exp, "%Y-%m-%d %H:%M:%S").astimezone(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
        expire_date = now + self.datetime.timedelta(days=exp)
        self.setVars(user_id, "EXPIRED_DATE", expire_date.strftime("%Y-%m-%d %H:%M:%S"))

    def getExp(self, user_id):
        expired_date = self.getVars(user_id, "EXPIRED_DATE")
        if expired_date:
            exp_datetime = self.datetime.datetime.strptime(expired_date, "%Y-%m-%d %H:%M:%S").astimezone(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
            return exp_datetime.strftime("%d-%m-%Y")
        else:
            return None

    def daysLeft(self, user_id):
        user_exp = self.getExp(user_id)
        today = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
        if user_exp:
            exp_datetime = self.datetime.datetime.strptime(user_exp, "%d-%m-%Y").astimezone(self.zoneinfo.ZoneInfo("Asia/Jakarta"))
            return (exp_datetime - today).days
        return None

    def checkAndDeleteIfExpired(self, user_id):
        user_exp = self.getExp(user_id)
        today = self.datetime.datetime.now(self.zoneinfo.ZoneInfo("Asia/Jakarta")).strftime("%d-%m-%Y")
        if not user_exp or user_exp == today:
            self.removeAllVars(user_id)
            self.removeBot(user_id)
            return True
        return False

    def saveBot(self, user_id, api_id, api_hash, value, is_token=False):
        field = "bot_token" if is_token else "session_string"
        encrypted_data = {
            "api_id": self.cipher.encrypt(str(api_id)),
            "api_hash": self.cipher.encrypt(api_hash),
            field: self.cipher.encrypt(value),
        }
        if self.storage_type == "mongo":
            self._mongo_save_bot(user_id, encrypted_data)
        elif self.storage_type == "sqlite":
            self._sqlite_set_bot(user_id, encrypted_data)
        else:
            data = self._load_data()
            entry = {"user_id": user_id, **encrypted_data}
            data["bots"].append(entry)
            self._save_data(data)

    def getBots(self, is_token=False):
        field = "bot_token" if is_token else "session_string"
        if self.storage_type == "mongo":
            bots = [
                {
                    "name": str(bot_data["user_id"]),
                    "api_id": int(self.cipher.decrypt(str(bot_data["api_id"]))),
                    "api_hash": self.cipher.decrypt(bot_data["api_hash"]),
                    field: self.cipher.decrypt(bot_data.get(field)),
                }
                for bot_data in self.data.bot.find({"user_id": {"$exists": 1}})
            ]
        elif self.storage_type == "sqlite":
            rows = self._sqlite_get_bots()
            bots = [
                {
                    "name": str(row[0]),
                    "api_id": int(self.cipher.decrypt(str(row[1]))),
                    "api_hash": self.cipher.decrypt(row[2]),
                    field: self.cipher.decrypt(row[3] if is_token else row[4]),
                }
                for row in rows
            ]
        else:
            bots = [
                {
                    "name": str(bot_data["user_id"]),
                    "api_id": int(self.cipher.decrypt(str(bot_data["api_id"]))),
                    "api_hash": self.cipher.decrypt(bot_data["api_hash"]),
                    field: self.cipher.decrypt(bot_data.get(field)),
                }
                for bot_data in self._load_data()["bots"]
            ]
        return bots

    def removeBot(self, user_id):
        if self.storage_type == "mongo":
            self._mongo_remove_bot(user_id)
        elif self.storage_type == "sqlite":
            self._sqlite_remove_bot(user_id)
        else:
            data = self._load_data()
            data["bots"] = [bot for bot in data["bots"] if bot["user_id"] != user_id]
            self._save_data(data)
