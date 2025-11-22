from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class VideoStreamInfo:
    url: str
    resolution: Tuple[int, int]
    duration: int


class PinterestMedia:
    def __init__(
        self,
        id: int,
        src: str,
        alt: Optional[str],
        origin: Optional[str],
        resolution: Tuple[int, int],
        video_stream: Optional[VideoStreamInfo] = None,
    ) -> None:
        self.id = id
        self.src = src
        self.alt = alt
        self.origin = origin
        self.resolution = resolution
        self.video_stream = video_stream
        self.local_path = None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "src": self.src,
            "alt": self.alt,
            "origin": self.origin,
            "resolution": {
                "x": self.resolution[0] if self.resolution else None,
                "y": self.resolution[1] if self.resolution else None,
            },
        }
        if self.video_stream:
            data["media_stream"] = {
                "video": {
                    "url": self.video_stream.url,
                    "resolution": self.video_stream.resolution,
                    "duration": self.video_stream.duration,
                }
            }
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "PinterestMedia":
        return PinterestMedia(
            data["id"],
            data["src"],
            data["alt"],
            data["origin"],
            (data["resolution"]["x"], data["resolution"]["y"]) if "resolution" in data else (0, 0),
            data.get("is_stream", False),
        )

    @classmethod
    def from_responses(
        cls,
        response_data: List[Dict[str, Any]],
        min_resolution: Tuple[int, int] = (0, 0),
        caption_from_title: bool = False,
    ) -> List["PinterestMedia"]:
        if not response_data:
            return []
        min_width, min_height = min_resolution

        images: List["PinterestMedia"] = []
        for item in response_data:
            if not isinstance(item, dict):
                continue

            orig = item.get("images", {}).get("orig")
            if not orig:
                continue

            try:
                width = int(orig.get("width", 0))
                height = int(orig.get("height", 0))
            except (TypeError, ValueError):
                continue

            if width < min_width or height < min_height:
                continue

            src = orig.get("url")
            if not src:
                continue
            id = item.get("id", 0)

            if caption_from_title:
                alt = item.get("title", item.get("auto_alt_text", ""))
            else:
                alt = item.get("auto_alt_text", "")

            origin = f"https://www.pinterest.com/pin/{id}/"

            is_stream = bool(item.get("should_open_in_stream", False))
            video_stream = None
            if is_stream:
                stream_variant = cls._get_best_video_variant(item)
                if stream_variant and stream_variant.get("url", None):
                    video_stream = VideoStreamInfo(
                        url=stream_variant["url"],
                        resolution=(stream_variant.get("width", 0), stream_variant.get("height", 0)),
                        duration=stream_variant.get("duration", 0),
                    )

            images.append(
                cls(
                    id,
                    src,
                    alt,
                    origin,
                    resolution=(width, height),
                    video_stream=video_stream,
                )
            )

        return images

    @staticmethod
    def _extract_video_list(data_raw: Dict[str, Any]) -> Dict[str, Dict]:
        try:
            video_list = data_raw["story_pin_data"]["pages"][0]["blocks"][0]["video"]["video_list"]
        except (KeyError, IndexError, TypeError):
            return {}
        if not isinstance(video_list, dict):
            return {}
        return video_list

    @staticmethod
    def _choose_highest_resolution(video_list: Dict[str, Dict]) -> Optional[Dict[str, Any]]:
        if not video_list:
            return None

        def resolution(entry: Dict[str, Any]) -> int:
            return (entry.get("width") or 0) * (entry.get("height") or 0)

        return max(video_list.values(), key=resolution)

    @classmethod
    def _get_best_video_variant(cls, data_raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        video_variant = cls._choose_highest_resolution(cls._extract_video_list(data_raw))
        if not video_variant:
            return None
        return video_variant
