import asyncio
import glob
import json
import os
import sqlite3
import zipfile
from datetime import datetime
from functools import partial
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
        self.backup_cron_spec = options.get("backup_cron_spec", "0 */3 * * *")
        self.scheduler = options.get("scheduler_instance")

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
                self._sync_save_data({"vars": {}, "bots": []})

        self._register_backup_task()

    async def _run_sync(self, func, *args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    def _register_backup_task(self):
        if self.auto_backup and self.scheduler and self.storage_type in ["local", "sqlite"]:

            if not self.backup_bot_token or not self.backup_chat_id:
                return self.cipher.log.warning("Auto backup is disabled because token/chat_id is missing.")

            @self.scheduler.cron(self.backup_cron_spec)
            async def scheduled_backup_task():
                self.cipher.log.info("Starting scheduled backup process...")
                await self.perform_backup()

    async def perform_backup(self):
        source_paths = []

        db_path = self.data_file if self.storage_type == "local" else self.db_file
        if await self._run_sync(os.path.exists, db_path):
            source_paths.append(db_path)
        else:
            self.cipher.log.warning("Database file not found. Skipping database backup.")

        env_files = await self._run_sync(glob.glob, "*.env")
        if env_files:
            source_paths.extend(env_files)

        if not source_paths:
            return self.cipher.log.warning("No files to back up. Aborting.")

        zip_path = None

        try:
            zip_path = await self._run_sync(self._create_zip_archive, source_paths)
            if zip_path:
                timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S %Z")

                caption = (
                    f"Backup otomatis untuk `{os.path.basename(zip_path)}`\n"
                    f"Tipe DB: `{self.storage_type}`\n"
                    f"Waktu: `{timestamp}`",
                )

                await self._send_zip_to_telegram(zip_path, caption)

        finally:
            if zip_path and await self._run_sync(os.path.exists, zip_path):
                await self._run_sync(os.remove, zip_path)

    def _create_zip_archive(self, source_paths: list):
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_{self.file_name}_{timestamp}.zip"

        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in source_paths:
                    zf.write(path, os.path.basename(path))

            return zip_filename

        except Exception as e:
            self.cipher.log.error(f"Failed to create ZIP archive: {e}")
            return None

    async def _send_zip_to_telegram(self, file_path, caption):
        url = f"https://api.telegram.org/bot{self.backup_bot_token}/sendDocument"

        try:
            with open(file_path, "rb") as doc:
                files = {"document": doc}
                params = {
                    "chat_id": self.backup_chat_id,
                    "caption": caption,
                    "parse_mode": "Markdown"
                }

                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(url, params=params, files=files)

            response.raise_for_status()
            response_data = response.json()

            if response_data.get("ok"):
                self.cipher.log.info("Successfully sent to Telegram.")
            else:
                self.cipher.log.error(f"Failed to send: {response_data.get('description')}")

        except Exception as e:
            self.cipher.log.error(f"Failed to send file to Telegram: {e}")

    def _sync_load_data(self):
        try:
            with open(self.data_file, "r") as f:
                return json.load(f)

        except (json.JSONDecodeError, FileNotFoundError):
            return {"vars": {}, "bots": []}

    def _sync_save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    async def _load_data(self):
        return await self._run_sync(self._sync_load_data)

    async def _save_data(self, data):
        await self._run_sync(self._sync_save_data, data)

    def __del__(self):
        self.close()

    async def close_async(self):
        await self._run_sync(self.close)

    def close(self):
        if self.storage_type == "sqlite" and hasattr(self, "conn") and self.conn:
            self.conn.close()

    def _initialize_sqlite(self):
        cursor = self.conn.cursor()

        cursor.execute("CREATE TABLE IF NOT EXISTS vars (user_id TEXT PRIMARY KEY, data TEXT)")

        cursor.execute(
            "CREATE TABLE IF NOT EXISTS bots (user_id TEXT PRIMARY KEY, api_id TEXT, api_hash TEXT, bot_token TEXT, session_string TEXT)"
        )

        self.conn.commit()

    async def _get_user_vars(self, user_id):
        user_id_str = str(user_id)

        if self.storage_type == "sqlite":
            row = await self._run_sync(
                lambda: self.conn.cursor().execute("SELECT data FROM vars WHERE user_id = ?", (user_id_str,)).fetchone()
            )

            return json.loads(self.cipher.decrypt(row[0])) if row else {}

        elif self.storage_type == "mongo":
            data = await self._run_sync(lambda: self.data.vars.find_one({"_id": user_id_str}))

            return data if data else {}

        else:
            data = await self._load_data()
            return data.get("vars", {}).get(user_id_str, {})

    async def _set_user_vars(self, user_id, user_data):
        user_id_str = str(user_id)

        if self.storage_type == "sqlite":
            encrypted_data = self.cipher.encrypt(json.dumps(user_data))

            await self._run_sync(
                lambda: (
                    self.conn.execute(
                        "INSERT OR REPLACE INTO vars (user_id, data) VALUES (?, ?)", (user_id_str, encrypted_data)
                    ),
                    self.conn.commit(),
                )
            )

        elif self.storage_type == "mongo":
            await self._run_sync(
                lambda: self.data.vars.update_one({"_id": user_id_str}, {"$set": user_data}, upsert=True)
            )

        else:
            full_data = await self._load_data()
            full_data.setdefault("vars", {})[user_id_str] = user_data
            await self._save_data(full_data)

    async def setVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))

        user_data = await self._get_user_vars(user_id)
        user_data.setdefault(var_key, {})[query_name] = encrypted_value

        await self._set_user_vars(user_id, user_data)

    async def getVars(self, user_id, query_name, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)

        encrypted_value = user_data.get(var_key, {}).get(query_name)
        if not encrypted_value:
            return None

        decrypted_str = self.cipher.decrypt(encrypted_value)

        try:
            return json.loads(decrypted_str)

        except (json.JSONDecodeError, TypeError):
            return decrypted_str

    async def removeVars(self, user_id, query_name, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)

        if user_data.get(var_key, {}).pop(query_name, None):
            await self._set_user_vars(user_id, user_data)

    async def setListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))

        user_data = await self._get_user_vars(user_id)

        user_data.setdefault(var_key, {}).setdefault(query_name, [])

        if encrypted_value not in user_data[var_key][query_name]:
            user_data[var_key][query_name].append(encrypted_value)
            await self._set_user_vars(user_id, user_data)

    async def getListVars(self, user_id, query_name, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)

        encrypted_list = user_data.get(var_key, {}).get(query_name, [])

        return [
            json.loads(self.cipher.decrypt(v)) if v.startswith(("[", "{")) else self.cipher.decrypt(v)
            for v in encrypted_list
        ]

    async def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        encrypted_value = self.cipher.encrypt(json.dumps(value) if isinstance(value, (dict, list)) else str(value))

        user_data = await self._get_user_vars(user_id)

        try:
            user_data.get(var_key, {}).get(query_name, []).remove(encrypted_value)
            await self._set_user_vars(user_id, user_data)

        except (ValueError, KeyError):
            pass

    async def removeAllVars(self, user_id):
        user_id_str = str(user_id)

        if self.storage_type == "sqlite":
            await self._run_sync(
                lambda: (
                    self.conn.execute("DELETE FROM vars WHERE user_id = ?", (user_id_str,)),
                    self.conn.commit(),
                )
            )

        elif self.storage_type == "mongo":
            await self._run_sync(lambda: self.data.vars.delete_one({"_id": user_id_str}))

        else:
            full_data = await self._load_data()
            full_data.get("vars", {}).pop(user_id_str, None)
            await self._save_data(full_data)

    async def allVars(self, user_id, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)

        encrypted_data = user_data.get(var_key, {})
        decrypted = {}

        for key, value in encrypted_data.items():

            if isinstance(value, list):
                temp_list = []

                for v in value:
                    decrypted_v_str = self.cipher.decrypt(v)

                    try:
                        temp_list.append(json.loads(decrypted_v_str))
                    except (json.JSONDecodeError, TypeError):
                        temp_list.append(decrypted_v_str)

                decrypted[key] = temp_list

            else:
                decrypted_v_str = self.cipher.decrypt(value)

                try:
                    decrypted[key] = json.loads(decrypted_v_str)
                except (json.JSONDecodeError, TypeError):
                    decrypted[key] = decrypted_v_str

        return decrypted

    async def saveBot(self, user_id, api_id, api_hash, value, is_token=False):
        user_id_str = str(user_id)

        field = "bot_token" if is_token else "session_string"

        bot_data = {"api_id": self.cipher.encrypt(str(api_id)), "api_hash": self.cipher.encrypt(api_hash)}

        if value:
            bot_data[field] = self.cipher.encrypt(value)

        if self.storage_type == "mongo":
            await self._run_sync(
                lambda: self.data.bot.update_one(
                    {"_id": user_id_str},
                    {"$set": bot_data},
                    upsert=True
                )
            )

        elif self.storage_type == "sqlite":
            await self._run_sync(
                lambda: (
                    self.conn.execute(
                        "INSERT OR REPLACE INTO bots (user_id, api_id, api_hash, bot_token, session_string) VALUES (?, ?, ?, ?, ?)",
                        (
                            user_id_str,
                            bot_data["api_id"],
                            bot_data["api_hash"],
                            bot_data.get("bot_token"),
                            bot_data.get("session_string"),
                        ),
                    ),
                    self.conn.commit(),
                )
            )

        else:
            data = await self._load_data()
            existing = next((b for b in data["bots"] if b.get("user_id") == user_id_str), None)

            if existing:
                existing.update(bot_data)
            else:
                data.setdefault("bots", []).append({"user_id": user_id_str, **bot_data})

            await self._save_data(data)

    async def getBots(self, is_token=False):
        raw_bots = []

        if self.storage_type == "mongo":
            raw_bots = await self._run_sync(lambda: list(self.data.bot.find()))

        elif self.storage_type == "sqlite":
            rows = await self._run_sync(
                lambda: self.conn.cursor()
                .execute("SELECT user_id, api_id, api_hash, bot_token, session_string FROM bots")
                .fetchall()
            )

            raw_bots = [
                {
                    "user_id": r[0],
                    "api_id": r[1],
                    "api_hash": r[2],
                    "bot_token": r[3],
                    "session_string": r[4]
                }
                for r in rows
            ]

        else:
            data = await self._load_data()
            raw_bots = data.get("bots", [])

        decrypted_bots = []

        for bot_data in raw_bots:
            try:
                decrypted = {"name": bot_data.get("user_id") or bot_data.get("_id")}

                for key in ["api_id", "api_hash", "bot_token", "session_string"]:
                    if bot_data.get(key):
                        value = self.cipher.decrypt(bot_data[key])
                        decrypted[key] = int(value) if key == "api_id" else value

                if (is_token and "bot_token" in decrypted) or (not is_token and "session_string" in decrypted):
                    decrypted_bots.append(decrypted)

            except (ValueError, TypeError):
                continue

        return decrypted_bots

    async def removeBot(self, user_id):
        user_id_str = str(user_id)

        if self.storage_type == "mongo":
            await self._run_sync(lambda: self.data.bot.delete_one({"_id": user_id_str}))

        elif self.storage_type == "sqlite":
            await self._run_sync(
                lambda: (
                    self.conn.execute("DELETE FROM bots WHERE user_id = ?", (user_id_str,)),
                    self.conn.commit(),
                )
            )

        else:
            data = await self._load_data()
            data["bots"] = [b for b in data["bots"] if b.get("user_id") != user_id_str]
            await self._save_data(data)
