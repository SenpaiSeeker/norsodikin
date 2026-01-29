import httpx
import asyncio
import base64
import mimetypes
import os

class PasteClient:
    def __init__(self, token: str):
        self.token = token
        self.post_url = "https://api.github.com/gists"

    async def paste(self, content, filename="paste.md", is_media=False, extension=None) -> str:
        final_content = ""
        
        if is_media:
            if isinstance(content, str) and os.path.exists(content):
                with open(content, "rb") as f:
                    file_data = f.read()
            elif isinstance(content, bytes):
                file_data = content
            else:
                raise ValueError("Content must be bytes or valid file path for media upload")

            b64_data = base64.b64encode(file_data).decode("utf-8")
            
            if extension:
                mime_guess = mimetypes.guess_type(f"file.{extension}")[0]
                mime_type = mime_guess if mime_guess else "application/octet-stream"
            else:
                mime_type = "application/octet-stream"

            if "image" in mime_type:
                final_content = f'<div align="center"><img src="data:{mime_type};base64,{b64_data}" alt="Uploaded Image" style="max-width: 100%; border-radius: 10px;"></div>'
            elif "video" in mime_type:
                final_content = f'<div align="center"><video controls style="max-width: 100%; border-radius: 10px;"><source src="data:{mime_type};base64,{b64_data}" type="{mime_type}">Your browser does not support the video tag.</video></div>'
            elif "audio" in mime_type:
                final_content = f'<div align="center"><audio controls style="width: 100%;"><source src="data:{mime_type};base64,{b64_data}" type="{mime_type}">Your browser does not support the audio element.</audio></div>'
            else:
                final_content = f"**Binary File**\nType: {mime_type}\nSize: {len(file_data)} bytes\n\n[Base64 Data Embedded]"
            
            filename = "preview.md"

        else:
            text_content = str(content)
            final_content = f"```text\n{text_content}\n```"

        payload = {
            "public": True,
            "files": {
                filename: {
                    "content": final_content
                }
            }
        }

        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json"
        }

        async with httpx.AsyncClient(headers=headers, timeout=120.0) as client:
            r = await client.post(self.post_url, json=payload)
            r.raise_for_status()
            return r.json()["html_url"]
