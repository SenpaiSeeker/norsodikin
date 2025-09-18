import asyncio
import os
import re
import httpx
import urllib.parse
from urllib.parse import urlparse, parse_qs
import fake_useragent

from ..utils.logger import LoggerHandler


class BingImageGenerator:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client
        self.base_url = "https://www.bing.com"

    async def get_images(self, prompt: str):
        url_encoded_prompt = urllib.parse.quote(prompt)
        creation_url = f"{self.base_url}/images/create?q={url_encoded_prompt}&rt=4&FORM=GENCRE"

        response = await self.client.get(creation_url)
        response.raise_for_status()

        if "PROMPT_BLOCKED" in str(response.url).upper():
             raise Exception("Your prompt has been blocked by Bing's content policy.")

        if "this prompt has been blocked" in response.text.lower():
             raise Exception("Your prompt has been blocked by Bing's content policy.")

        response_text = response.text
        if "Enforce user status failed." in response_text:
            raise Exception("Authentication failed. Please check your cookies.")
            
        result_url = response.url
        parsed_url = urlparse(str(result_url))
        query_params = parse_qs(parsed_url.query)
        
        if not query_params.get("id"):
             raise Exception("Could not find generation ID in the response.")

        polling_url = f"{self.base_url}/images/create/async/results/{query_params['id'][0]}"

        for _ in range(10):
            await asyncio.sleep(3)
            poll_response = await self.client.get(polling_url)
            poll_response.raise_for_status()
            
            if poll_response.status_code == 200 and ".jpeg" in poll_response.text:
                image_urls = re.findall(r'src="([^"]+)"', poll_response.text)
                return [url.split("?")[0] for url in image_urls]
        
        raise Exception("Image generation timed out.")


class ImageGenerator:
    def __init__(self, cookies_file_path: str = "cookies.txt", logging_enabled: bool = True):
        self.cookies = self._parse_cookie_file(cookies_file_path)
        self.client = self._create_client()
        self.generator = BingImageGenerator(self.client)
        self.logging_enabled = logging_enabled
        self.log = LoggerHandler()
    
    def _parse_cookie_file(self, file_path: str) -> dict:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Cookie file not found: {file_path}")

        cookies_dict = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.strip().startswith("#"):
                    continue
                parts = line.strip().split("\t")
                if len(parts) >= 7 and ".bing.com" in parts[0]:
                    cookies_dict[parts[5]] = parts[6]
        
        required = ['_U', 'SRCHUSR', 'KievRPSSecAuth']
        if not all(c in cookies_dict for c in required):
            raise ValueError(f"One of the required cookies ({', '.join(required)}) is missing.")
            
        return cookies_dict

    def _create_client(self) -> httpx.AsyncClient:
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "max-age=0",
            "content-type": "application/x-www-form-urlencoded",
            "referrer": "https://www.bing.com/images/create/",
            "user-agent": fake_useragent.UserAgent().random
        }

        return httpx.AsyncClient(
            headers=headers,
            cookies=self.cookies,
            follow_redirects=True,
            timeout=200
        )
        
    def __log(self, message: str):
        if self.logging_enabled:
            self.log.print(message)

    async def generate(self, prompt: str):
        self.__log(f"{self.log.GREEN}Starting image generation for prompt: '{prompt}'")
        try:
            image_urls = await self.generator.get_images(prompt)
            self.__log(f"{self.log.GREEN}Successfully generated {len(image_urls)} images.")
            return image_urls
        except Exception as e:
            self.__log(f"{self.log.RED}Image generation failed: {e}")
            raise e
