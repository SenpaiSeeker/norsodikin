import asyncio
import json
import os
import shutil
import sqlite3
import sys
import zipfile
from datetime import datetime
from functools import partial
from zoneinfo import ZoneInfo

import aiofiles
import aiohttp

from ..code.encrypt import CipherHandler


class DataBase:
    def __init__(self, **options):
        self.storage_type = options.get("storage_type", "local")
        self.file_name = options.get("file_name", "database")
        self.keys_encrypt = options.get("keys_encrypt", "default_db_key_12345")
        self.method_encrypt = options.get("method_encrypt", "bytes")
        self.cipher = CipherHandler(key=self.keys_encrypt, method=self.method_encrypt)

        self._lock = asyncio.Lock()

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
                with open(self.data_file, "w") as f:
                    json.dump({"vars": {}, "bots": []}, f, indent=4)

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
                asyncio.create_task(self.perform_backup())

    async def perform_backup(self):
        async with self._lock:
            db_path = self.data_file if self.storage_type == "local" else self.db_file

            if not await self._run_sync(os.path.exists, db_path):
                self.cipher.log.warning("Database file not found for backup.")
                return

            temp_backup_dir = "temp_db_backup"
            if not os.path.exists(temp_backup_dir):
                os.makedirs(temp_backup_dir)

            try:
                temp_db_path = os.path.join(temp_backup_dir, os.path.basename(db_path))
                await self._run_sync(shutil.copy2, db_path, temp_db_path)

                zip_path = await self._run_sync(self._create_zip_archive, temp_db_path, temp_backup_dir)

                if zip_path:
                    timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S %Z")
                    caption = (
                        f"Backup otomatis untuk `{os.path.basename(zip_path)}`\n"
                        f"Tipe DB: `{self.storage_type}`\n"
                        f"Waktu: `{timestamp}`"
                    )
                    await self._send_zip_to_telegram(zip_path, caption)
            except Exception as e:
                self.cipher.log.error(f"Backup failed: {e}")
            finally:
                await self._run_sync(shutil.rmtree, temp_backup_dir, ignore_errors=True)
                if zip_path and os.path.exists(zip_path):
                    try:
                        os.remove(zip_path)
                    except:
                        pass

    def _create_zip_archive(self, source_path: str, temp_dir: str):
        timestamp = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y%m%d_%H%M%S")
        zip_filename = f"backup_{self.file_name}_{timestamp}.zip"
        try:
            with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zf:
                arcname = os.path.basename(source_path)
                zf.write(source_path, arcname)
            return zip_filename
        except Exception as e:
            self.cipher.log.error(f"Failed to create ZIP: {e}")
            return None

    async def _send_zip_to_telegram(self, file_path, caption):
        url = f"https://api.telegram.org/bot{self.backup_bot_token}/sendDocument"
        data = aiohttp.FormData()
        data.add_field("chat_id", str(self.backup_chat_id))
        data.add_field("caption", caption)
        data.add_field("parse_mode", "Markdown")
        data.add_field("document", open(file_path, "rb"))

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=data) as resp:
                    resp_data = await resp.json()
                    if resp_data.get("ok"):
                        self.cipher.log.info("Successfully sent backup to Telegram.")
                    else:
                        self.cipher.log.error(f"Failed to send backup: {resp_data.get('description')}")
            except Exception as e:
                self.cipher.log.error(f"Failed to send file to Telegram: {e}")

    async def _load_data(self):
        async with self._lock:
            try:
                async with aiofiles.open(self.data_file, "r") as f:
                    content = await f.read()
                    if not content.strip():
                        return {"vars": {}, "bots": []}
                    return json.loads(content)
            except (FileNotFoundError, json.JSONDecodeError):
                return {"vars": {}, "bots": []}

    async def _save_data(self, data):
        async with self._lock:
            temp_file = f"{self.data_file}.tmp"
            async with aiofiles.open(temp_file, "w") as f:
                await f.write(json.dumps(data, indent=4))

            await self._run_sync(os.replace, temp_file, self.data_file)

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
        val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(val_str)
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
        val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(val_str)
        user_data = await self._get_user_vars(user_id)
        user_data.setdefault(var_key, {}).setdefault(query_name, [])
        if encrypted_value not in user_data[var_key][query_name]:
            user_data[var_key][query_name].append(encrypted_value)
            await self._set_user_vars(user_id, user_data)

    async def getListVars(self, user_id, query_name, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)
        encrypted_list = user_data.get(var_key, {}).get(query_name, [])
        decoded_list = []
        for v in encrypted_list:
            decrypted = self.cipher.decrypt(v)
            try:
                decoded_list.append(json.loads(decrypted) if decrypted.startswith(("[", "{")) else decrypted)
            except:
                decoded_list.append(decrypted)
        return decoded_list

    async def removeListVars(self, user_id, query_name, value, var_key="variabel"):
        val_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        encrypted_value = self.cipher.encrypt(val_str)
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
            if user_id_str in full_data.get("vars", {}):
                del full_data["vars"][user_id_str]
                await self._save_data(full_data)

    async def allVars(self, user_id, var_key="variabel"):
        user_data = await self._get_user_vars(user_id)
        encrypted_data = user_data.get(var_key, {})
        decrypted = {}
        for key, value in encrypted_data.items():
            if isinstance(value, list):
                temp_list = []
                for v in value:
                    try:
                        decrypted_v = self.cipher.decrypt(v)
                        temp_list.append(json.loads(decrypted_v) if decrypted_v.startswith(("[", "{")) else decrypted_v)
                    except:
                        temp_list.append(v)
                decrypted[key] = temp_list
            else:
                try:
                    decrypted_v = self.cipher.decrypt(value)
                    decrypted[key] = json.loads(decrypted_v) if decrypted_v.startswith(("[", "{")) else decrypted_v
                except:
                    decrypted[key] = value
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
                    upsert=True,
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
            full_data = await self._load_data()
            bots_list = full_data.get("bots", [])
            existing_index = next((index for (index, d) in enumerate(bots_list) if d.get("user_id") == user_id_str), -1)

            if existing_index != -1:
                bots_list[existing_index].update(bot_data)
            else:
                new_entry = {"user_id": user_id_str, **bot_data}
                bots_list.append(new_entry)

            full_data["bots"] = bots_list
            await self._save_data(full_data)

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
                    "session_string": r[4],
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
                    val = bot_data.get(key)
                    if val:
                        dec_val = self.cipher.decrypt(val)
                        decrypted[key] = int(dec_val) if key == "api_id" else dec_val

                if (is_token and "bot_token" in decrypted) or (not is_token and "session_string" in decrypted):
                    decrypted_bots.append(decrypted)
            except:
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
            full_data = await self._load_data()
            full_data["bots"] = [b for b in full_data.get("bots", []) if b.get("user_id") != user_id_str]
            await self._save_data(full_data)
