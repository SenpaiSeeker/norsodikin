class ShellExecutor:
    def __init__(self):
        self.asyncio = __import__("asyncio")

    async def run(self, command: str):
        process = await self.asyncio.create_subprocess_shell(
            command, stdout=self.asyncio.subprocess.PIPE, stderr=self.asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return (stdout.decode("utf-8").strip(), stderr.decode("utf-8").strip(), process.returncode)
