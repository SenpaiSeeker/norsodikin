import asyncio
import os
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx


class PinterestAPIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class PinterestRateLimitError(PinterestAPIError):
    pass


class PinterestAuthenticationError(PinterestAPIError):
    pass


class PinterestNotFoundError(PinterestAPIError):
    pass


class PinterestAPI:
    def __init__(self, access_token: Optional[str] = None):
        self.base_url = "https://api.pinterest.com/v5"
        self.access_token = access_token
        self.client: Optional[httpx.AsyncClient] = None
        
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def close(self):
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def _handle_response(self, response: httpx.Response) -> Dict:
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 204:
            return {}
        elif response.status_code == 400:
            raise PinterestAPIError("Bad Request", 400, response.json())
        elif response.status_code == 401:
            raise PinterestAuthenticationError("Unauthorized - Invalid or expired access token", 401, response.json())
        elif response.status_code == 403:
            raise PinterestAuthenticationError("Forbidden - Insufficient permissions", 403, response.json())
        elif response.status_code == 404:
            raise PinterestNotFoundError("Resource not found", 404, response.json())
        elif response.status_code == 429:
            raise PinterestRateLimitError("Rate limit exceeded", 429, response.json())
        else:
            raise PinterestAPIError(f"HTTP {response.status_code}", response.status_code, response.json())
    
    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                      json_data: Optional[Dict] = None) -> Dict:
        client = await self._get_client()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=json_data
            )
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise PinterestAPIError(f"Request failed: {str(e)}")
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str, 
                                     client_id: str, client_secret: str) -> Dict:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        client = await self._get_client()
        auth = (client_id, client_secret)
        
        try:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data=data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise PinterestAPIError(f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str, client_id: str, 
                                   client_secret: str, continuous_refresh: bool = True) -> Dict:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "continuous_refresh": str(continuous_refresh).lower()
        }
        
        client = await self._get_client()
        auth = (client_id, client_secret)
        
        try:
            response = await client.post(
                f"{self.base_url}/oauth/token",
                data=data,
                auth=auth,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            return await self._handle_response(response)
        except httpx.RequestError as e:
            raise PinterestAPIError(f"Token refresh failed: {str(e)}")
    
    def set_access_token(self, access_token: str):
        self.access_token = access_token
    
    async def get_user_account(self) -> Dict:
        return await self._request("GET", "/user_account")
    
    async def get_user_analytics(self, start_date: str, end_date: str, 
                                 metric_types: Optional[List[str]] = None,
                                 split_field: Optional[str] = None,
                                 app_types: Optional[str] = None) -> Dict:
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if metric_types:
            params["metric_types"] = ",".join(metric_types)
        if split_field:
            params["split_field"] = split_field
        if app_types:
            params["app_types"] = app_types
            
        return await self._request("GET", "/user_account/analytics", params=params)
    
    async def list_boards(self, page_size: Optional[int] = None, 
                         bookmark: Optional[str] = None,
                         privacy: Optional[str] = None) -> Dict:
        params = {}
        if page_size:
            params["page_size"] = page_size
        if bookmark:
            params["bookmark"] = bookmark
        if privacy:
            params["privacy"] = privacy
            
        return await self._request("GET", "/boards", params=params)
    
    async def get_board(self, board_id: str) -> Dict:
        return await self._request("GET", f"/boards/{board_id}")
    
    async def create_board(self, name: str, description: Optional[str] = None,
                          privacy: str = "PUBLIC") -> Dict:
        data = {
            "name": name,
            "privacy": privacy
        }
        if description:
            data["description"] = description
            
        return await self._request("POST", "/boards", json_data=data)
    
    async def update_board(self, board_id: str, name: Optional[str] = None,
                          description: Optional[str] = None,
                          privacy: Optional[str] = None) -> Dict:
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if privacy:
            data["privacy"] = privacy
            
        return await self._request("PATCH", f"/boards/{board_id}", json_data=data)
    
    async def delete_board(self, board_id: str) -> Dict:
        return await self._request("DELETE", f"/boards/{board_id}")
    
    async def list_pins(self, page_size: Optional[int] = None,
                       bookmark: Optional[str] = None) -> Dict:
        params = {}
        if page_size:
            params["page_size"] = page_size
        if bookmark:
            params["bookmark"] = bookmark
            
        return await self._request("GET", "/pins", params=params)
    
    async def get_pin(self, pin_id: str) -> Dict:
        return await self._request("GET", f"/pins/{pin_id}")
    
    async def create_pin(self, board_id: str, media: Dict,
                        title: Optional[str] = None,
                        description: Optional[str] = None,
                        link: Optional[str] = None,
                        alt_text: Optional[str] = None) -> Dict:
        data = {
            "board_id": board_id,
            "media": media
        }
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if link:
            data["link"] = link
        if alt_text:
            data["alt_text"] = alt_text
            
        return await self._request("POST", "/pins", json_data=data)
    
    async def update_pin(self, pin_id: str, title: Optional[str] = None,
                        description: Optional[str] = None,
                        link: Optional[str] = None,
                        alt_text: Optional[str] = None,
                        board_id: Optional[str] = None) -> Dict:
        data = {}
        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if link:
            data["link"] = link
        if alt_text:
            data["alt_text"] = alt_text
        if board_id:
            data["board_id"] = board_id
            
        return await self._request("PATCH", f"/pins/{pin_id}", json_data=data)
    
    async def delete_pin(self, pin_id: str) -> Dict:
        return await self._request("DELETE", f"/pins/{pin_id}")
    
    async def list_board_pins(self, board_id: str, page_size: Optional[int] = None,
                             bookmark: Optional[str] = None) -> Dict:
        params = {}
        if page_size:
            params["page_size"] = page_size
        if bookmark:
            params["bookmark"] = bookmark
            
        return await self._request("GET", f"/boards/{board_id}/pins", params=params)
    
    async def search_partner_pins(self, query: str, page_size: Optional[int] = None,
                                 bookmark: Optional[str] = None) -> Dict:
        params = {"query": query}
        if page_size:
            params["page_size"] = page_size
        if bookmark:
            params["bookmark"] = bookmark
            
        return await self._request("GET", "/search/partner_pins", params=params)
    
    async def get_pin_analytics(self, pin_id: str, start_date: str, end_date: str,
                               metric_types: Optional[List[str]] = None,
                               split_field: Optional[str] = None,
                               app_types: Optional[str] = None) -> Dict:
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if metric_types:
            params["metric_types"] = ",".join(metric_types)
        if split_field:
            params["split_field"] = split_field
        if app_types:
            params["app_types"] = app_types
            
        return await self._request("GET", f"/pins/{pin_id}/analytics", params=params)
    
    async def get_board_analytics(self, board_id: str, start_date: str, end_date: str,
                                 metric_types: Optional[List[str]] = None,
                                 split_field: Optional[str] = None,
                                 app_types: Optional[str] = None) -> Dict:
        params = {
            "start_date": start_date,
            "end_date": end_date
        }
        if metric_types:
            params["metric_types"] = ",".join(metric_types)
        if split_field:
            params["split_field"] = split_field
        if app_types:
            params["app_types"] = app_types
            
        return await self._request("GET", f"/boards/{board_id}/analytics", params=params)
    
    async def list_all_pins(self, max_items: Optional[int] = None) -> List[Dict]:
        all_pins = []
        bookmark = None
        
        while True:
            response = await self.list_pins(bookmark=bookmark)
            items = response.get("items", [])
            all_pins.extend(items)
            
            if max_items and len(all_pins) >= max_items:
                return all_pins[:max_items]
            
            bookmark = response.get("bookmark")
            if not bookmark:
                break
                
        return all_pins
    
    async def list_all_boards(self, max_items: Optional[int] = None) -> List[Dict]:
        all_boards = []
        bookmark = None
        
        while True:
            response = await self.list_boards(bookmark=bookmark)
            items = response.get("items", [])
            all_boards.extend(items)
            
            if max_items and len(all_boards) >= max_items:
                return all_boards[:max_items]
            
            bookmark = response.get("bookmark")
            if not bookmark:
                break
                
        return all_boards
    
    async def list_all_board_pins(self, board_id: str, max_items: Optional[int] = None) -> List[Dict]:
        all_pins = []
        bookmark = None
        
        while True:
            response = await self.list_board_pins(board_id, bookmark=bookmark)
            items = response.get("items", [])
            all_pins.extend(items)
            
            if max_items and len(all_pins) >= max_items:
                return all_pins[:max_items]
            
            bookmark = response.get("bookmark")
            if not bookmark:
                break
                
        return all_pins
    
    async def batch_create_pins(self, pins_data: List[Dict]) -> List[Dict]:
        results = []
        for pin_data in pins_data:
            try:
                result = await self.create_pin(**pin_data)
                results.append({"success": True, "data": result})
            except PinterestAPIError as e:
                results.append({"success": False, "error": str(e), "status_code": e.status_code})
        return results
    
    async def retry_on_rate_limit(self, func, *args, max_retries: int = 3, 
                                 base_delay: float = 1.0, **kwargs) -> Any:
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except PinterestRateLimitError:
                if attempt == max_retries - 1:
                    raise
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
    def create_media_object(self, media_type: str, source_type: str, 
                           url: Optional[str] = None,
                           data: Optional[str] = None,
                           title: Optional[str] = None,
                           description: Optional[str] = None,
                           duration: Optional[float] = None,
                           height: Optional[int] = None,
                           width: Optional[int] = None) -> Dict:
        media = {
            "media_type": media_type
        }
        
        if source_type == "image_url" and url:
            media["source"] = {
                "source_type": "image_url",
                "url": url
            }
        elif source_type == "image_base64" and data:
            media["source"] = {
                "source_type": "image_base64",
                "data": data
            }
        elif source_type == "video_url" and url:
            media["source"] = {
                "source_type": "video_url",
                "url": url
            }
            
        if title:
            media["title"] = title
        if description:
            media["description"] = description
        if duration:
            media["duration"] = duration
        if height:
            media["height"] = height
        if width:
            media["width"] = width
            
        return media
    
    async def extract_pin_id_from_url(self, url: str) -> Optional[str]:
        patterns = [
            r'pinterest\.com/pin/(\d+)',
            r'pin\.it/(\w+)',
            r'/pin/(\d+)/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                pin_id = match.group(1)
                if not pin_id.isdigit():
                    resolved_url = await self._resolve_short_url(url)
                    if resolved_url:
                        return await self.extract_pin_id_from_url(resolved_url)
                return pin_id
        return None
    
    async def _resolve_short_url(self, short_url: str) -> Optional[str]:
        client = await self._get_client()
        try:
            response = await client.get(short_url, follow_redirects=True)
            return str(response.url)
        except Exception:
            return None
    
    async def get_pin_from_url(self, url: str) -> Dict:
        pin_id = await self.extract_pin_id_from_url(url)
        if not pin_id:
            raise PinterestAPIError("Invalid Pinterest URL - could not extract pin ID")
        return await self.get_pin(pin_id)
    
    async def get_media_urls_from_pin(self, pin_data: Dict) -> Dict[str, Any]:
        media_urls = {
            "images": [],
            "videos": [],
            "media_type": None
        }
        
        if "media" in pin_data:
            media = pin_data["media"]
            media_urls["media_type"] = media.get("media_type", "unknown")
            
            if "images" in media:
                for size, image_data in media["images"].items():
                    if isinstance(image_data, dict) and "url" in image_data:
                        media_urls["images"].append({
                            "size": size,
                            "url": image_data["url"],
                            "width": image_data.get("width"),
                            "height": image_data.get("height")
                        })
            
            if "video_url" in media:
                media_urls["videos"].append({
                    "url": media["video_url"],
                    "type": "video"
                })
        
        return media_urls
    
    async def download_media(self, url: str, save_path: str) -> Dict[str, Any]:
        client = await self._get_client()
        
        try:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                f.write(response.content)
            
            return {
                "success": True,
                "path": save_path,
                "size": len(response.content),
                "url": url
            }
        except Exception as e:
            raise PinterestAPIError(f"Download failed: {str(e)}")
    
    async def download_pin_media(self, pin_id: str, save_dir: str, 
                                 quality: str = "originals") -> List[Dict]:
        pin_data = await self.get_pin(pin_id)
        media_urls = await self.get_media_urls_from_pin(pin_data)
        
        downloaded_files = []
        
        for idx, image_data in enumerate(media_urls["images"]):
            if image_data["size"] == quality or (quality == "best" and idx == 0):
                filename = f"{pin_id}_{image_data['size']}.jpg"
                file_path = f"{save_dir}/{filename}"
                
                try:
                    result = await self.download_media(image_data["url"], file_path)
                    downloaded_files.append(result)
                except Exception as e:
                    downloaded_files.append({
                        "success": False,
                        "error": str(e),
                        "url": image_data["url"]
                    })
        
        for idx, video_data in enumerate(media_urls["videos"]):
            filename = f"{pin_id}_video_{idx}.mp4"
            file_path = f"{save_dir}/{filename}"
            
            try:
                result = await self.download_media(video_data["url"], file_path)
                downloaded_files.append(result)
            except Exception as e:
                downloaded_files.append({
                    "success": False,
                    "error": str(e),
                    "url": video_data["url"]
                })
        
        return downloaded_files
    
    async def download_from_url(self, pinterest_url: str, save_dir: str, 
                                quality: str = "originals") -> List[Dict]:
        pin_id = await self.extract_pin_id_from_url(pinterest_url)
        if not pin_id:
            raise PinterestAPIError("Invalid Pinterest URL")
        
        return await self.download_pin_media(pin_id, save_dir, quality)
    
    async def search_and_download(self, query: str, save_dir: str, 
                                  max_items: int = 10,
                                  quality: str = "originals") -> List[Dict]:
        search_results = await self.search_partner_pins(query, page_size=max_items)
        pins = search_results.get("items", [])
        
        all_downloads = []
        for pin in pins[:max_items]:
            pin_id = pin.get("id")
            if pin_id:
                try:
                    downloads = await self.download_pin_media(pin_id, save_dir, quality)
                    all_downloads.extend(downloads)
                except Exception as e:
                    all_downloads.append({
                        "success": False,
                        "pin_id": pin_id,
                        "error": str(e)
                    })
        
        return all_downloads
    
    async def get_best_quality_url(self, pin_id: str) -> Optional[str]:
        pin_data = await self.get_pin(pin_id)
        media_urls = await self.get_media_urls_from_pin(pin_data)
        
        if media_urls["images"]:
            for img in media_urls["images"]:
                if img["size"] == "originals" or img["size"] == "orig":
                    return img["url"]
            return media_urls["images"][0]["url"]
        
        if media_urls["videos"]:
            return media_urls["videos"][0]["url"]
        
        return None
    
    async def bulk_download_from_urls(self, urls: List[str], save_dir: str,
                                     quality: str = "originals") -> List[Dict]:
        all_results = []
        for url in urls:
            try:
                results = await self.download_from_url(url, save_dir, quality)
                all_results.extend(results)
            except Exception as e:
                all_results.append({
                    "success": False,
                    "url": url,
                    "error": str(e)
                })
        
        return all_results
    
    async def search_images(self, query: str, page_size: Optional[int] = None,
                           bookmark: Optional[str] = None) -> Dict:
        return await self.search_partner_pins(query, page_size, bookmark)
    
    async def get_downloadable_media_info(self, pin_id: str) -> Dict:
        pin_data = await self.get_pin(pin_id)
        media_urls = await self.get_media_urls_from_pin(pin_data)
        
        return {
            "pin_id": pin_id,
            "title": pin_data.get("title", ""),
            "description": pin_data.get("description", ""),
            "link": pin_data.get("link", ""),
            "media_type": media_urls["media_type"],
            "images": media_urls["images"],
            "videos": media_urls["videos"],
            "download_ready": len(media_urls["images"]) > 0 or len(media_urls["videos"]) > 0
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
