import httpx

class TelegramPH:
    def __init__(self, timeout: float = 15.0):
        self.api_url = "https://api.telegra.ph"
        self.upload_url = "https://telegra.ph/upload"
        self.timeout = timeout

    async def create_account(self, short_name: str, author_name: str = "nsdev") -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.get(
                f"{self.api_url}/createAccount", 
                params={"short_name": short_name, "author_name": author_name}
            )
            res.raise_for_status()
            data = res.json()
            if data.get("ok"):
                return data["result"]["access_token"]
            raise Exception(data.get("error", "Gagal membuat akun Telegraph"))

    async def create_page(self, access_token: str, title: str, content: list) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            res = await client.post(
                f"{self.api_url}/createPage", 
                json={"access_token": access_token, "title": title, "content": content}
            )
            res.raise_for_status()
            data = res.json()
            if data.get("ok"):
                return data["result"]["path"]
            raise Exception(data.get("error", "Gagal membuat halaman Telegraph"))

    async def upload_json(self, short_name: str, author_name: str, title: str, json_string: str, chunk_size: int = 30000) -> str:
        token = await self.create_account(short_name=short_name, author_name=author_name)
        content_nodes =[
            {"tag": "p", "children": [json_string[i:i+chunk_size]]} 
            for i in range(0, len(json_string), chunk_size)
        ]
        return await self.create_page(access_token=token, title=title, content=content_nodes)

    async def upload_image(self, file_data) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if isinstance(file_data, bytes):
                files = {"file": ("image.png", file_data, "image/png")}
                res = await client.post(self.upload_url, files=files)
            else:
                with open(file_data, "rb") as f:
                    files = {"file": ("image.png", f, "image/png")}
                    res = await client.post(self.upload_url, files=files)
            
            res.raise_for_status()
            data = res.json()
            
            if isinstance(data, list) and len(data) > 0 and "src" in data[0]:
                return "https://telegra.ph" + data[0]["src"]
            if isinstance(data, dict) and "error" in data:
                raise Exception(data["error"])
                
            raise Exception("Gagal mengunggah gambar ke Telegra.ph")
