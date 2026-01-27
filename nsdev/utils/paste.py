import httpx
import re
import uuid
import html
from html.parser import HTMLParser

class TelegraphHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.current_node = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag == "br":
            return

        node = {"tag": tag, "children": []}
        if attrs:
            node["attrs"] = dict(attrs)
        
        if self.current_node:
            self.current_node["children"].append(node)
            self.stack.append(self.current_node)
        else:
            self.nodes.append(node)
        
        self.current_node = node

    def handle_endtag(self, tag):
        if tag == "br":
            return
            
        if self.stack:
            self.current_node = self.stack.pop()
        else:
            self.current_node = None

    def handle_data(self, data):
        clean_data = html.unescape(data)
        if not clean_data:
            return

        if self.current_node:
            self.current_node["children"].append(clean_data)
        else:
            if clean_data.strip():
                self.nodes.append({"tag": "p", "children": [clean_data]})

class PasteClient:
    def __init__(self, timeout: int = 30):
        self.base_url = "https://api.graph.org"
        self.timeout = timeout
        self.access_token = None

    async def _get_access_token(self, client):
        if self.access_token:
            return self.access_token
            
        try:
            response = await client.get(
                f"{self.base_url}/createAccount",
                params={
                    "short_name": "NSUserBot",
                    "author_name": "NS Userbot",
                    "author_url": "https://t.me/telegram"
                },
                timeout=self.timeout
            )
            data = response.json()
            if data.get("ok"):
                self.access_token = data["result"]["access_token"]
                return self.access_token
            raise Exception(f"Gagal membuat akun Telegraph: {data}")
        except Exception as e:
            raise Exception(f"Error koneksi Telegraph: {e}")

    def _format_content(self, text: str) -> str:
        text = re.sub(r'```([\s\S]*?)```', r'<pre>\1</pre>', text)
        text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.*?)__', r'<i>\1</i>', text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        
        if "<" not in text and ">" not in text:
            text = text.replace("\n", "<br>")
            
        return text

    def _convert_text_to_nodes(self, text: str):
        html_text = self._format_content(text)
        
        parser = TelegraphHTMLParser()
        parser.feed(html_text)
        
        if not parser.nodes:
            return [{"tag": "p", "children": [text]}]
            
        return parser.nodes

    async def paste(self, text: str, extension: str = "txt", title: str = "NSUserBot") -> str:
        async with httpx.AsyncClient() as client:
            token = await self._get_access_token(client)
            
            content_nodes = self._convert_text_to_nodes(text)
            
            random_suffix = uuid.uuid4().hex[:6]
            final_title = f"{title}-{random_suffix}"

            payload = {
                "access_token": token,
                "title": final_title,
                "content": content_nodes,
                "return_content": False
            }

            try:
                response = await client.post(
                    f"{self.base_url}/createPage",
                    json=payload,
                    timeout=self.timeout
                )
                result = response.json()

                if result.get("ok"):
                    return result["result"]["url"]
                else:
                    error_msg = result.get('error', 'Unknown Error')
                    
                    fallback_payload = {
                        "access_token": token,
                        "title": final_title + " (Raw)",
                        "content": [{"tag": "pre", "children": [text]}],
                        "return_content": False
                    }
                    fb_resp = await client.post(f"{self.base_url}/createPage", json=fallback_payload)
                    fb_result = fb_resp.json()
                    
                    if fb_result.get("ok"):
                        return fb_result["result"]["url"]
                    
                    raise Exception(f"Telegraph API Error: {error_msg}")

            except Exception as e:
                raise Exception(f"Gagal upload ke Telegraph: {e}")
