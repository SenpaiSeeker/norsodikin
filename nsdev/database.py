class DataBase:
    def __init__(self, **options):
        """
        Inisialisasi database dengan parameter opsional.
        :param options:
            - storage_type: 'local' (default) atau 'mongo'
            - file_name: Nama file untuk database lokal (default: 'database')
            - binary_keys: Kunci enkripsi untuk CipherHandler (default: 14151819154911914)
            - method_encrypt: metode enkripsi untuk CipherHandler (default: bytes)
            - mongo_url: URL MongoDB (untuk storage_type='mongo')
            - git_repo_path: Path untuk operasi git (default: '.')
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
        self.git_repo_path = options.get("git_repo_path", ".")

        if self.storage_type == "mongo":
            self.pymongo = __import__("pymongo")
            self.mongo_url = options.get("mongo_url")
            if not self.mongo_url:
                raise ValueError("mongo_url is required for MongoDB storage")
            self.client = self.pymongo.MongoClient(self.mongo_url)
            self.data = self.client[self.file_name]
        else:
            self.data_file = f"{self.file_name}.json"
            self._initialize_files()

        self.cipher = __import__("nsdev").encrypt.CipherHandler(key=self.binary_keys, method=self.method_encrypt)

    def _initialize_files(self):
        if not self.os.path.exists(self.data_file):
            self._save_data({"vars": {}, "bots": []})

    def _load_data(self):
        if self.storage_type == "mongo":
            raise RuntimeError("_load_data is not applicable for MongoDB storage")
        try:
            with open(self.data_file, "r") as f:
                content = f.read()
                return self.json.loads(content) if content.strip() else {"vars": {}, "bots": []}
        except (self.json.JSONDecodeError, FileNotFoundError):
            return {"vars": {}, "bots": []}

    def _save_data(self, data):
        if self.storage_type == "mongo":
            raise RuntimeError("_save_data is not applicable for MongoDB storage")
        with open(self.data_file, "w") as f:
            self.json.dump(data, f, indent=4)

    def setVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            update_data = {"$set": {f"{var_key}.{query_name}": encrypted_value}}
            self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)
        else:
            data = self._load_data()
            user_data = data["vars"].setdefault(str(user_id), {})
            user_data[var_key] = user_data.get(var_key, {})
            user_data[var_key][query_name] = encrypted_value
            self._save_data(data)

    def getVars(self, user_id, query_name, var_key="variabel"):
        if self.storage_type == "mongo":
            result = self.data.vars.find_one({"_id": user_id})
            encrypted_value = result.get(var_key, {}).get(query_name, None) if result else None
        else:
            encrypted_value = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name)
        return self.cipher.decrypt(encrypted_value) if encrypted_value else None

    def setListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            result = self.data.vars.find_one({"_id": user_id})
            existing_values = result.get(var_key, {}).get(query_name, []) if result else []
            if encrypted_value not in existing_values:
                update_data = {"$push": {f"{var_key}.{query_name}": encrypted_value}}
                self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)
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
            result = self.data.vars.find_one({"_id": user_id})
            encrypted_values = result.get(var_key, {}).get(query_name, []) if result else []
        else:
            encrypted_values = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name, [])
        return [self.cipher.decrypt(value) for value in encrypted_values]

    def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(value)
        if self.storage_type == "mongo":
            result = self.data.vars.find_one({"_id": user_id})
            existing_values = result.get(var_key, {}).get(query_name, []) if result else []
            if encrypted_value in existing_values:
                update_data = {"$pull": {f"{var_key}.{query_name}": encrypted_value}}
                self.data.vars.update_one({"_id": user_id}, update_data)
        else:
            data = self._load_data()
            user_data = data.get("vars", {}).get(str(user_id), {}).get(var_key, {})
            if query_name in user_data and encrypted_value in user_data[query_name]:
                user_data[query_name].remove(encrypted_value)
                self._save_data(data)

    def removeAllVars(self, user_id, var_key="variabel"):
        if self.storage_type == "mongo":
            update_data = {"$unset": {var_key: ""}}
            self.data.vars.update_one({"_id": user_id}, update_data)
        else:
            data = self._load_data()
            data["vars"].pop(str(user_id), None)
            self._save_data(data)

    def allVars(self, user_id, var_key="variabel"):
        if self.storage_type == "mongo":
            result = self.data.vars.find_one({"_id": user_id})
            encrypted_data = result.get(var_key, {}) if result else {}
        else:
            encrypted_data = self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {})
        return {key: self.cipher.decrypt(value) for key, value in encrypted_data.items()}

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
            filter_query = {"user_id": user_id}
            update_data = {"$set": encrypted_data}
            self.data.bot.update_one(filter_query, update_data, upsert=True)
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
            self.data.bot.delete_one({"user_id": user_id})
        else:
            data = self._load_data()
            data["bots"] = [bot for bot in data["bots"] if bot["user_id"] != user_id]
            self._save_data(data)
