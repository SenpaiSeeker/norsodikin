import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime


class InboxChecker:
    BASE_URL = "https://api.mail.tm"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_messages(self, token: str) -> List[Dict[str, Any]]:
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with session.get(
                f"{self.BASE_URL}/messages",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('hydra:member', [])
        except Exception as e:
            print(f"Error fetching messages: {e}")
        
        return []
    
    async def get_message_detail(self, token: str, message_id: str) -> Optional[Dict[str, Any]]:
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with session.get(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception as e:
            print(f"Error fetching message detail: {e}")
        
        return None
    
    async def delete_message(self, token: str, message_id: str) -> bool:
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with session.delete(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=headers
            ) as response:
                return response.status == 204
        except Exception as e:
            print(f"Error deleting message: {e}")
        
        return False
    
    async def mark_as_seen(self, token: str, message_id: str) -> bool:
        session = await self._get_session()
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            async with session.patch(
                f"{self.BASE_URL}/messages/{message_id}",
                headers=headers,
                json={"seen": True}
            ) as response:
                return response.status == 200
        except Exception as e:
            print(f"Error marking message as seen: {e}")
        
        return False
