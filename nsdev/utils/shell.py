import asyncio


class ShellExecutor:
    async def run(self, command: str):
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return (stdout.decode("utf-8").strip(), stderr.decode("utf-8").strip(), process.returncode)
