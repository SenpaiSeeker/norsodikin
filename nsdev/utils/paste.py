import httpx
import json
import os
import base64
import mimetypes

class PasteClient:
    def __init__(self, token: str):
        self.token = token
        self.post_url = "https://api.github.com/gists"

    async def paste(self, content, extension="md"):
        description = "Uploaded via NSUserBot"
        
        if isinstance(content, (list, dict, tuple)):
            try:
                final_content = json.dumps(content, indent=4, default=str)
                extension = "json"
            except Exception:
                final_content = str(content)
        
        elif isinstance(content, bytes):
            try:
                final_content = content.decode("utf-8")
            except UnicodeDecodeError:
                final_content = base64.b64encode(content).decode("utf-8")
                extension = "txt"

        elif os.path.exists(str(content)):
            file_path = str(content)
            mime_type, _ = mimetypes.guess_type(file_path)
            
            if mime_type and (mime_type.startswith("image") or mime_type.startswith("video") or mime_type.startswith("audio")):
                with open(file_path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                
                media_tag = ""
                if mime_type.startswith("image"):
                    media_tag = f'<img src="data:{mime_type};base64,{b64_data}" style="max-width: 100%; height: auto; display: block; margin: 0 auto;">'
                elif mime_type.startswith("video"):
                    media_tag = f'<video controls style="max-width: 100%; height: auto; display: block; margin: 0 auto;"><source src="data:{mime_type};base64,{b64_data}" type="{mime_type}">Browser tidak mendukung tag video.</video>'
                elif mime_type.startswith("audio"):
                    media_tag = f'<audio controls style="width: 100%; display: block; margin: 20px auto;"><source src="data:{mime_type};base64,{b64_data}" type="{mime_type}">Browser tidak mendukung tag audio.</audio>'

                final_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Preview</title>
    <style>
        body {{ background-color: #0d1117; color: #c9d1d9; font-family: -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; margin: 0; padding: 20px; }}
        .container {{ background: #161b22; padding: 20px; border-radius: 6px; border: 1px solid #30363d; box-shadow: 0 0 10px rgba(0,0,0,0.5); max-width: 90%; }}
        h2 {{ text-align: center; color: #58a6ff; }}
        p {{ text-align: center; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>NSUserBot Media Preview</h2>
        <p>Filename: {os.path.basename(file_path)} | Type: {mime_type}</p>
        {media_tag}
    </div>
</body>
</html>"""
                extension = "html"
                description = "Media Embedded (Download/View Raw to see content)"
            
            else:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        final_content = f.read()
                    file_ext = os.path.splitext(file_path)[1]
                    if file_ext:
                        extension = file_ext.lstrip(".")
                except UnicodeDecodeError:
                    with open(file_path, "rb") as f:
                        final_content = base64.b64encode(f.read()).decode("utf-8")
                    extension = "txt"
        
        else:
            final_content = str(content)

        if not final_content:
            return "No content to paste"

        filename = f"paste.{extension}"

        payload = {
            "public": True,
            "description": description,
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

        async with httpx.AsyncClient(headers=headers, timeout=60.0) as client:
            r = await client.post(self.post_url, json=payload)
            r.raise_for_status()
            response_json = r.json()
            return response_json
