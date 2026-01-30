import asyncssh


class RemoteExecutor:
    async def connect_and_run(
        self, host: str, username: str, command: str, password: str = None, private_key: str = None, port: int = 22
    ):
        try:
            conn_options = {"host": host, "port": port, "username": username, "known_hosts": None}

            if password:
                conn_options["password"] = password
            if private_key:
                conn_options["client_keys"] = [private_key]

            async with asyncssh.connect(**conn_options) as conn:
                result = await conn.run(command, check=False)

                output = result.stdout.strip()
                error = result.stderr.strip()
                exit_code = result.exit_status

                return {"stdout": output, "stderr": error, "exit_code": exit_code, "success": exit_code == 0}

        except (OSError, asyncssh.Error) as e:
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "success": False}

    async def check_connection(self, host: str, username: str, password: str = None, port: int = 22):
        try:
            conn_options = {"host": host, "port": port, "username": username, "known_hosts": None}
            if password:
                conn_options["password"] = password

            async with asyncssh.connect(**conn_options) as conn:
                return True
        except Exception:
            return False
