#  _      ____   _____          _        _____       _______       ____           _____ ______  #
# | |    / __ \ / ____|   /\   | |      |  __ \   /\|__   __|/\   |  _ \   /\    / ____|  ____| #
# | |   | |  | | |       /  \  | |      | |  | | /  \  | |  /  \  | |_) | /  \  | (___ | |__    #
# | |   | |  | | |      / /\ \ | |      | |  | |/ /\ \ | | / /\ \ |  _ < / /\ \  \___ \|  __|   #
# | |___| |__| | |____ / ____ \| |____  | |__| / ____ \| |/ ____ \| |_) / ____ \ ____) | |____  #
# |______\____/ \_____/_/    \_\______| |_____/_/    \_\_/_/    \_\____/_/    \_\_____/|______| #


class LocalDataBase:
    def __init__(self, file_name: str = "database", binary_keys: int = 14151819154911914):
        self.os = __import__("os")
        self.json = __import__("json")
        self.datetime = __import__("datetime")
        self.pytz = __import__("pytz")
        self.subprocess = __import__("subprocess")
        self.binary = __import__("nsdev").encrypt.BinaryCipher(binary_keys)
        self.data_file = f"{file_name}.json"
        self.git_repo_path = "."
        self._initialize_files()

    def setVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        data = self._load_data()
        user_data = data["vars"].setdefault(str(user_id), {var_key: {}})
        user_data[var_key][query_name] = value
        self._save_data(data)

    def getVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        return self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name)

    def removeVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        data = self._load_data()
        if str(user_id) in data["vars"]:
            data["vars"][str(user_id)][var_key].pop(query_name, None)
            self._save_data(data)

    def setListVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        data = self._load_data()
        user_data = data["vars"].setdefault(str(user_id), {var_key: {}})
        user_data[var_key].setdefault(query_name, []).append(value)
        self._save_data(data)

    def getListVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        return self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {}).get(query_name, [])

    def removeListVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        data = self._load_data()
        user_data = data.get("vars", {}).get(str(user_id), {}).get(var_key, {})
        if query_name in user_data and value in user_data[query_name]:
            user_data[query_name].remove(value)
            self._save_data(data)

    def removeAllVars(self, user_id: int):
        data = self._load_data()
        data["vars"].pop(str(user_id), None)
        self._save_data(data)

    def allVars(self, user_id: int, var_key: str = "variabel"):
        return self._load_data().get("vars", {}).get(str(user_id), {}).get(var_key, {})

    def saveBot(self, user_id: int, api_id: int, api_hash: str, value: str, is_token: bool = False):
        data = self._load_data()
        field = "bot_token" if is_token else "session_string"
        entry = {
            "user_id": user_id,
            "api_id": self.binary.encrypt(str(api_id)),
            "api_hash": self.binary.encrypt(api_hash),
            field: self.binary.encrypt(value),
        }
        data["bots"].append(entry)
        self._save_data(data)

    def getBots(self, is_token: bool = False):
        field = "bot_token" if is_token else "session_string"
        return [
            {
                "name": str(bot_data["user_id"]),
                "api_id": int(self.binary.decrypt(str(bot_data["api_id"]))),
                "api_hash": self.binary.decrypt(bot_data["api_hash"]),
                field: self.binary.decrypt(bot_data.get(field)),
            }
            for bot_data in self._load_data()["bots"]
            if bot_data.get(field)
        ]

    def removeBot(self, user_id: int):
        data = self._load_data()
        data["bots"] = [bot for bot in data["bots"] if bot["user_id"] != user_id]
        self._save_data(data)

    def setExp(self, user_id: int, exp: int = 30):
        have_exp = self.getVars(user_id, "EXPIRED_DATE")

        if not have_exp:
            now = self.datetime.datetime.now(self.pytz.timezone("Asia/Jakarta"))
        else:
            now = self.datetime.datetime.strptime(have_exp, "%Y-%m-%d %H:%M:%S").astimezone(self.pytz.timezone("Asia/Jakarta"))

        expire_date = now + self.datetime.timedelta(days=exp)
        self.setVars(user_id, "EXPIRED_DATE", expire_date.strftime("%Y-%m-%d %H:%M:%S"))

    def getExp(self, user_id: int):
        expired_date = self.getVars(user_id, "EXPIRED_DATE")

        if expired_date:
            exp_datetime = self.datetime.datetime.strptime(expired_date, "%Y-%m-%d %H:%M:%S").astimezone(self.pytz.timezone("Asia/Jakarta"))
            return exp_datetime.strftime("%d-%m-%Y")
        else:
            return None

    def _initialize_files(self):
        if not self.os.path.exists(self.data_file):
            self._save_data({"vars": {}, "bots": []})

    def _load_data(self):
        try:
            with open(self.data_file, "r") as f:
                return self.json.load(f)
        except self.json.JSONDecodeError:
            return {"vars": {}, "bots": []}

    def _save_data(self, data):
        with open(self.data_file, "w") as f:
            self.json.dump(data, f, indent=4)

    def _git_commit(self, username: str, token: str, message: str = "auto commit backup database"):
        try:
            self.subprocess.run(["git", "add", self.data_file], cwd=self.git_repo_path, check=True)
            self.subprocess.run(["git", "commit", "-m", message], cwd=self.git_repo_path, check=True)

            push_command = f'echo "{username}:{token}" | git push'
            self.subprocess.run(push_command, shell=True, cwd=self.git_repo_path, check=True)
            return "Backup committed and pushed successfully."
        except self.subprocess.CalledProcessError as e:
            return f"Error during git operations: {e}"


#  __  __  ____  _   _  _____  ____    _____       _______       ____           _____ ______  #
# |  \/  |/ __ \| \ | |/ ____|/ __ \  |  __ \   /\|__   __|/\   |  _ \   /\    / ____|  ____| #
# | \  / | |  | |  \| | |  __| |  | | | |  | | /  \  | |  /  \  | |_) | /  \  | (___ | |__    #
# | |\/| | |  | | . ` | | |_ | |  | | | |  | |/ /\ \ | | / /\ \ |  _ < / /\ \  \___ \|  __|   #
# | |  | | |__| | |\  | |__| | |__| | | |__| / ____ \| |/ ____ \| |_) / ____ \ ____) | |____  #
# |_|  |_|\____/|_| \_|\_____|\____/  |_____/_/    \_\_/_/    \_\____/_/    \_\_____/|______| #


class MongoDataBase:
    def __init__(self, mongo_url: str, file_name: str = "database", bytes_keys: int = 14151819154911914):
        self.pymongo = __import__("pymongo")
        self.nsdev = __import__("nsdev")
        self.datetime = __import__("datetime")
        self.pytz = __import__("pytz")

        self.client = self.pymongo.MongoClient(mongo_url)
        self.data = self.client[file_name]
        self.bytes = self.nsdev.encrypt.BytesCipher(bytes_keys)

    def setVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        update_data = {"$set": {f"{var_key}.{query_name}": value}}
        self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)

    def getVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        result = self.data.vars.find_one({"_id": user_id})
        return result.get(var_key, {}).get(query_name, None) if result else None

    def removeVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        update_data = {"$unset": {f"{var_key}.{query_name}": ""}}
        self.data.vars.update_one({"_id": user_id}, update_data)

    def setListVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        update_data = {"$push": {f"{var_key}.{query_name}": value}}
        self.data.vars.update_one({"_id": user_id}, update_data, upsert=True)

    def getListVars(self, user_id: int, query_name: str, var_key: str = "variabel"):
        result = self.data.vars.find_one({"_id": user_id})
        return result.get(var_key, {}).get(query_name, []) if result else []

    def removeListVars(self, user_id: int, query_name: str, value: str, var_key: str = "variabel"):
        update_data = {"$pull": {f"{var_key}.{query_name}": value}}
        self.data.vars.update_one({"_id": user_id}, update_data)

    def removeAllVars(self, user_id: int, var_key: str = "variabel"):
        update_data = {"$unset": {var_key: ""}}
        self.data.vars.update_one({"_id": user_id}, update_data)

    def allVars(self, user_id: int, var_key: str = "variabel"):
        result = self.data.vars.find_one({"_id": user_id})
        return result.get(var_key, {}) if result else {}

    def setExp(self, user_id: int, exp: int = 30):
        have_exp = self.getVars(user_id, "EXPIRED_DATE")

        if not have_exp:
            now = self.datetime.datetime.now(self.pytz.timezone("Asia/Jakarta"))
        else:
            now = self.datetime.datetime.strptime(have_exp, "%Y-%m-%d %H:%M:%S").astimezone(self.pytz.timezone("Asia/Jakarta"))

        expire_date = now + self.datetime.timedelta(days=exp)
        self.setVars(user_id, "EXPIRED_DATE", expire_date.strftime("%Y-%m-%d %H:%M:%S"))

    def getExp(self, user_id: int):
        expired_date = self.getVars(user_id, "EXPIRED_DATE")

        if expired_date:
            exp_datetime = self.datetime.datetime.strptime(expired_date, "%Y-%m-%d %H:%M:%S").astimezone(self.pytz.timezone("Asia/Jakarta"))
            return exp_datetime.strftime("%d-%m-%Y")
        else:
            return None

    def saveBot(self, user_id: int, api_id: int, api_hash: str, value: str, is_token: bool = False):
        update_data = {
            "$set": {
                "api_id": self.bytes.encrypt(str(api_id)),
                "api_hash": self.bytes.encrypt(api_hash),
                "bot_token" if is_token else "session_string": self.bytes.encrypt(value),
            }
        }
        return self.data.bot.update_one({"user_id": user_id}, update_data, upsert=True)

    def getBots(self, is_token: bool = False):
        field = "bot_token" if is_token else "session_string"
        return [
            {
                "name": str(bot_data["user_id"]),
                "api_id": int(self.bytes.decrypt(str(bot_data["api_id"]))),
                "api_hash": self.bytes.decrypt(bot_data["api_hash"]),
                field: self.bytes.decrypt(bot_data.get(field)),
            }
            for bot_data in self.data.bot.find({"user_id": {"$exists": 1}})
        ]

    def removeBot(self, user_id: int):
        return self.data.bot.delete_one({"user_id": user_id})
