import asyncio
import json
import os
import sqlite3
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from ..code.encrypt import CipherHandler


class DataBase:
    def __init__(self, **options):
        self.storage_type = options.get("storage_type", "local")
        self.file_name = options.get("file_name", "database")
        self.keys_encrypt = options.get("keys_encrypt", "default_db_key_12345")
        self.method_encrypt = options.get("method_encrypt", "bytes")
        self.cipher = CipherHandler(key=self.keys_encrypt, method=self.method_encrypt)
        
        self.auto_backup = options.get("auto_backup", False)
        self.backup_bot_token = options.get("backup_bot_token")
        self.backup_chat_id = options.get("backup_chat_id")
        self.backup_interval_hours = options.get("backup_interval_hours", 24)
        self._backup_task = None

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
            self._initialize_sqlite()
        else:
            self.data_file = f"{self.file_name}.json"
            if not os.path.exists(self.data_file):
                self._save_data({"vars": {}, "bots": []})
        
        if self.auto_backup and self.storage_type in ["local", "sqlite"]:
            if not self.backup_bot_token or not self.backup_chat_id:
                self.cipher.log.print(
                    f"{self.cipher.log.YELLOW}[BACKUP] Auto backup dinonaktifkan karena token/chat_id tidak ada."
                )
            else:
                self._start_backup_task()

    def _start_backup_task(self):
        if self._backup_task is None or self._backup_task.done():
            self.cipher.log.print(
                f"{self.cipher.log.GREEN}[BACKUP] Task backup dijadwalkan setiap {self.backup_interval_hours} jam."
            )
            self._backup_task = asyncio.create_task(self._backup_looper())

    async def _backup_looper(self):
        interval_seconds = self.backup_interval_hours * 3600
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                self.cipher.log.print(f"{self.cipher.log.CYAN}[BACKUP] Memulai proses backup terjadwal...")
                await self._perform_backup()
            except asyncio.CancelledError:
                self.cipher.log.print(f"{self.cipher.log.YELLOW}[BACKUP] Task backup dihentikan.")
                break
            except Exception as e:
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Terjadi error pada loop backup: {e}")

    async def _perform_backup(self):
        source_path = self.data_file if self.storage_type == "local" else self.db_file
        if not os.path.exists(source_path):
            self.cipher.log.print(f"{self.cipher.log.YELLOW}[BACKUP] File database tidak ditemukan. Backup dilewati.")
            return

        loop = asyncio.get_running_loop()
        try:
            zip_path = await loop.run_in_executor(None, self._create_zip_archive, source_path)
            if zip_path:
                timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
                caption = f"Backup otomatis untuk `{self.file_name}`\nTipe: `{self.storage_type}`\nWaktu: `{timestamp} WIB`"
                await self._send_zip_to_telegram(zip_path, caption)
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
    
    def _create_zip_archive(self, source_path):
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_{self.file_name}_{timestamp}.zip"
        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(source_path, os.path.basename(source_path))
            return zip_filename
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal membuat arsip ZIP: {e}")
            return None

    async def _send_zip_to_telegram(self, file_path, caption):
        url = f"https://api.telegram.org/bot{self.backup_bot_token}/sendDocument"
        try:
            with open(file_path, "rb") as doc:
                files = {"document": doc}
                params = {"chat_id": self.backup_chat_id, "caption": caption, "parse_mode": "Markdown"}
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(url, params=params, files=files)
            
            response.raise_for_status()
            response_data = response.json()
            if response_data.get("ok"):
                self.cipher.log.print(f"{self.cipher.log.GREEN}[BACKUP] Berhasil dikirim ke Telegram.")
            else:
                self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal mengirim: {response_data.get('description')}")
        except Exception as e:
            self.cipher.log.print(f"{self.cipher.log.RED}[BACKUP] Gagal mengirim file ke Telegram: {e}")

    def _load_data(self):
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"vars": {}, "bots": []}

    def _save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    def __del__(self):
        self.close()

    async def close_async(self):
        if self._backup_task and not self._backup_task.done():
            self._backup_task.cancel()
            try:
                await self._backup_task
            except asyncio.CancelledError:
                pass 
        self.close()

    def close(self):
        if self.storage_type == "sqlite" and hasattr(self, "conn") and self.conn:
            self.conn.close()

    def _initialize_sqlite(self):
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS vars (user_id TEXT PRIMARY KEY, data TEXT)")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bots (
                user_id TEXT PRIMARY KEY, api_id TEXT, api_hash TEXT,
                bot_token TEXT, session_string TEXT
            )
        """)
        self.conn.commit()
        
    def _get_user_vars(self, user_id):
        user_id_str = str(user_id)
        if self.storage_type == 'sqlite':
            cursor = self.conn.cursor()
            cursor.execute("SELECT data FROM vars WHERE user_id = ?", (user_id_str,))
            row = cursor.fetchone()
            return json.loads(self.cipher.decrypt(row[0])) if row else {}
        elif self.storage_type == 'mongo':
            data = self.data.vars.find_one({"_id": user_id_str})
            return data if data else {}
        else: # local
            return self._load_data().get("vars", {}).get(user_id_str, {})
            
    def _set_user_vars(self, user_id, user_data):
        user_id_str = str(user_id)
        if self.storage_type == 'sqlite':
            encrypted_data = self.cipher.encrypt(json.dumps(user_data))
            self.conn.execute("INSERT OR REPLACE INTO vars (user_id, data) VALUES (?, ?)", (user_id_str, encrypted_data))
            self.conn.commit()
        elif self.storage_type == 'mongo':
            self.data.vars.update_one({"_id": user_id_str}, {"$set": user_data}, upsert=True)
        else: # local
            full_data = self._load_data()
            full_data["vars"][user_id_str] = user_data
            self._save_data(full_data)

    def setVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        user_data = self._get_user_vars(user_id)
        if var_key not in user_data: user_data[var_key] = {}
        user_data[var_key][query_name] = encrypted_value
        self._set_user_vars(user_id, user_data)
        
    def getVars(self, user_id, query_name, var_key="variabel"):
        user_data = self._get_user_vars(user_id)
        encrypted_value = user_data.get(var_key, {}).get(query_name)
        if not encrypted_value: return None
        decrypted_str = self.cipher.decrypt(encrypted_value)
        try:
            return json.loads(decrypted_str)
        except (json.JSONDecodeError, TypeError):
            return decrypted_str

    def removeVars(self, user_id, query_name, var_key="variabel"):
        user_data = self._get_user_vars(user_id)
        if user_data.get(var_key, {}).pop(query_name, None):
            self._set_user_vars(user_id, user_data)

    def setListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        user_data = self._get_user_vars(user_id)
        if var_key not in user_data: user_data[var_key] = {}
        if query_name not in user_data[var_key]: user_data[var_key][query_name] = []
        if encrypted_value not in user_data[var_key][query_name]:
            user_data[var_key][query_name].append(encrypted_value)
            self._set_user_vars(user_id, user_data)

    def getListVars(self, user_id, query_name, var_key="variabel"):
        user_data = self._get_user_vars(user_id)
        encrypted_list = user_data.get(var_key, {}).get(query_name, [])
        return [self.cipher.decrypt(v) for v in encrypted_list]

    def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))
        user_data = self._get_user_vars(user_id)
        try:
            user_data.get(var_key, {}).get(query_name, []).remove(encrypted_value)
            self._set_user_vars(user_id, user_data)
        except (ValueError, KeyError):
            pass

    def removeAllVars(self, user_id):
        user_id_str = str(user_id)
        if self.storage_type == "sqlite":
            self.conn.execute("DELETE FROM vars WHERE user_id = ?", (user_id_str,))
            self.conn.commit()
        elif self.storage_type == "mongo":
            self.data.vars.delete_one({"_id": user_id_str})
        else:
            full_data = self._load_data()
            full_data.get("vars", {}).pop(user_id_str, None)
            self._save_data(full_data)

    def saveBot(self, user_id, api_id, api_hash, value, is_token=False):
        user_id_str = str(user_id)
        field = "bot_token" if is_token else "session_string"
        bot_data = {
            "api_id": self.cipher.encrypt(str(api_id)),
            "api_hash": self.cipher.encrypt(api_hash),
        }
        if value: bot_data[field] = self.cipher.encrypt(value)
        
        if self.storage_type == "mongo":
            self.data.bot.update_one({"_id": user_id_str}, {"$set": bot_data}, upsert=True)
        elif self.storage_type == "sqlite":
            self.conn.execute("""
                INSERT OR REPLACE INTO bots (user_id, api_id, api_hash, bot_token, session_string) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id_str, bot_data["api_id"], bot_data["api_hash"], bot_data.get("bot_token"), bot_data.get("session_string")))
            self.conn.commit()
        else:
            data = self._load_data()
            existing = next((b for b in data["bots"] if b.get("user_id") == user_id_str), None)
            if existing: existing.update(bot_data)
            else: data["bots"].append({"user_id": user_id_str, **bot_data})
            self._save_data(data)
            
    def getBots(self, is_token=False):
        raw_bots = []
        if self.storage_type == "mongo":
            raw_bots = self.data.bot.find()
        elif self.storage_type == "sqlite":
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id, api_id, api_hash, bot_token, session_string FROM bots")
            raw_bots = [{"user_id": r[0], "api_id": r[1], "api_hash": r[2], "bot_token": r[3], "session_string": r[4]} for r in cursor.fetchall()]
        else: # local
            raw_bots = self._load_data().get("bots", [])

        decrypted_bots = []
        for bot_data in raw_bots:
            try:
                decrypted = {"name": bot_data.get("user_id") or bot_data.get("_id")}
                for key in ["api_id", "api_hash", "bot_token", "session_string"]:
                    if bot_data.get(key):
                        decrypted[key] = self.cipher.decrypt(bot_data[key])
                if is_token and decrypted.get("bot_token"):
                    decrypted_bots.append(decrypted)
                elif not is_token and decrypted.get("session_string"):
                    decrypted_bots.append(decrypted)
            except (ValueError, TypeError): continue
        return decrypted_bots
        
    def removeBot(self, user_id):
        user_id_str = str(user_id)
        if self.storage_type == "mongo":
            self.data.bot.delete_one({"_id": user_id_str})
        elif self.storage_type == "sqlite":
            self.conn.execute("DELETE FROM bots WHERE user_id = ?", (user_id_str,))
            self.conn.commit()
        else:
            data = self._load_data()
            data["bots"] = [b for b in data["bots"] if b.get("user_id") != user_id_str]
            self._save_data(data)
