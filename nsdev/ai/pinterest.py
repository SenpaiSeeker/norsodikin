import requests
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Pinner:
    username: str
    full_name: str
    follower_count: int
    image_small_url: str

@dataclass
class Board:
    id: str
    name: str
    url: str
    pin_count: int

@dataclass
class PinterestItem:
    pin: str
    link: Optional[str]
    created_at: str
    id: str
    image_url: str
    video_url: Optional[str]
    gif_url: Optional[str]
    grid_title: str
    description: str
    type: str
    pinner: Pinner
    board: Board
    reaction_counts: Dict[str, int]
    dominant_color: str
    seo_alt_text: str

@dataclass
class PinterestResponse:
    status: bool
    data: List[PinterestItem]
    timestamp: str

class PinterestAPI:
    def __init__(self):
        self.base_url = "https://api.siputzx.my.id/api/s/pinterest"
        self.session = requests.Session()
        self.session.headers.update({
            'accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search(self, query: str, type: str = "image") -> PinterestResponse:
        """
        Search Pinterest content
        
        Args:
            query (str): Search query
            type (str): Content type - 'video', 'gif', or 'image'
        
        Returns:
            PinterestResponse: Response object containing search results

        Example:
            pinterest = PinterestAPI()            
            try:
                result = pinterest.search("cat", "image")
                if result.status:
                    print(f"Found {len(result.data)} results")
                    print(f"Timestamp: {result.timestamp}")
                    
                    for i, item in enumerate(result.data[:5]):
                        print(f"\n--- Result {i+1} ---")
                        print(f"Title: {item.grid_title}")
                        print(f"Type: {item.type}")
                        print(f"Image URL: {item.image_url}")
                        print(f"Pinner: {item.pinner.full_name} (@{item.pinner.username})")
                        print(f"Reactions: {sum(item.reaction_counts.values())}")
                        print(f"Description: {item.description[:100]}...")
                    
                    # Filter hanya image
                    images = pinterest.filter_by_type(result.data, "image")
                    print(f"\nTotal images: {len(images)}")
                    
                    # Sort by reactions
                    sorted_by_popularity = pinterest.sort_by_reactions(images)
                    print(f"Most popular has {sum(sorted_by_popularity[0].reaction_counts.values())} reactions")
                    
                else:
                    print("No results found")
                    
            except Exception as e:
                print(f"Error: {e}")
        """
        try:
            params = {
                'query': query,
                'type': type
            }
            
            response = self.session.get(self.base_url, params=params)
            response.raise_for_status()
            
            json_data = response.json()
            
            return self._parse_response(json_data)
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Pinterest API error: {e}")
    
    def _parse_response(self, json_data: dict) -> PinterestResponse:
        """Parse JSON response to PinterestResponse object"""
        data_list = []
        
        for item in json_data.get('data', []):
            pinner_data = item.get('pinner', {})
            pinner = Pinner(
                username=pinner_data.get('username', ''),
                full_name=pinner_data.get('full_name', ''),
                follower_count=pinner_data.get('follower_count', 0),
                image_small_url=pinner_data.get('image_small_url', '')
            )            
            board_data = item.get('board', {})
            board = Board(
                id=board_data.get('id', ''),
                name=board_data.get('name', ''),
                url=board_data.get('url', ''),
                pin_count=board_data.get('pin_count', 0)
            )            
            pinterest_item = PinterestItem(
                pin=item.get('pin', ''),
                link=item.get('link'),
                created_at=item.get('created_at', ''),
                id=item.get('id', ''),
                image_url=item.get('image_url', ''),
                video_url=item.get('video_url'),
                gif_url=item.get('gif_url'),
                grid_title=item.get('grid_title', ''),
                description=item.get('description', ''),
                type=item.get('type', ''),
                pinner=pinner,
                board=board,
                reaction_counts=item.get('reaction_counts', {}),
                dominant_color=item.get('dominant_color', ''),
                seo_alt_text=item.get('seo_alt_text', '')
            )
            
            data_list.append(pinterest_item)
        
        return PinterestResponse(
            status=json_data.get('status', False),
            data=data_list,
            timestamp=json_data.get('timestamp', '')
        )
    
    def filter_by_type(self, items: List[PinterestItem], type: str) -> List[PinterestItem]:
        """Filter items by type"""
        return [item for item in items if item.type == type]
    
    def sort_by_reactions(self, items: List[PinterestItem], ascending: bool = False) -> List[PinterestItem]:
        """Sort items by total reactions"""
        def get_total_reactions(item):
            return sum(item.reaction_counts.values())
        
        return sorted(items, key=get_total_reactions, reverse=not ascending)
    
    def get_image_urls(self, items: List[PinterestItem]) -> List[str]:
        """Extract all image URLs from items"""
        return [item.image_url for item in items if item.image_url]
    
    def get_video_urls(self, items: List[PinterestItem]) -> List[str]:
        """Extract all video URLs from items"""
        return [item.video_url for item in items if item.video_url]