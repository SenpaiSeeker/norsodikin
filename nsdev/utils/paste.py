import httpx
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

            html_template = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Media Preview</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #0d1117; color: #c9d1d9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
                    .container { text-align: center; padding: 20px; background: #161b22; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.5); border: 1px solid #30363d; max-width: 90%; }
                    img, video, audio { max-width: 100%; border-radius: 8px; margin-top: 10px; }
                    .info { margin-bottom: 15px; font-size: 0.9em; color: #8b949e; }
                    a.btn { display: inline-block; margin-top: 15px; padding: 8px 16px; background: #238636; color: white; text-decoration: none; border-radius: 6px; font-size: 14px; font-weight: 600; }
                    a.btn:hover { background: #2ea043; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="info">Media Type: {mime_type} | Size: {size} bytes</div>
                    {media_tag}
                    <br>
                    <a href="{data_uri}" download="downloaded_file.{ext}" class="btn">Download File</a>
                </div>
            </body>
            </html>
            """
            
            data_uri = f"data:{mime_type};base64,{b64_data}"
            media_tag = ""

            if "image" in mime_type:
                media_tag = f'<img src="{data_uri}" alt="Preview">'
            elif "video" in mime_type:
                media_tag = f'<video controls autoplay muted><source src="{data_uri}" type="{mime_type}">Browser not supported.</video>'
            elif "audio" in mime_type:
                media_tag = f'<audio controls><source src="{data_uri}" type="{mime_type}">Browser not supported.</audio>'
            else:
                media_tag = f'<div style="padding: 50px; background: #21262d; border-radius: 8px;">BINARY FILE PREVIEW NOT AVAILABLE</div>'

            final_content = html_template.format(
                mime_type=mime_type,
                size=len(file_data),
                media_tag=media_tag,
                data_uri=data_uri,
                ext=extension or "bin"
            )
            
            filename = "index.html"

        else:
            text_content = str(content)
            final_content = f"```text\n{text_content}\n```"

        payload = {
            "description": "Uploaded via NSUserBot Tools",
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
            raw_url = r.json()["html_url"]
            
            if is_media:
                user = r.json()["owner"]["login"]
                gist_id = r.json()["id"]
                raw_file_url = f"https://gist.githubusercontent.com/{user}/{gist_id}/raw/index.html"
                return f"https://htmlpreview.github.io/?{raw_file_url}"
            
            return raw_url
