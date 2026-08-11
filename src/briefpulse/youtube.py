"""YouTube Data API v3, key-only. Two cheap calls per creator (1 unit each):
channels.list?forHandle → uploads playlist id, then playlistItems.list → latest videos.
Never search.list (100 units/call)."""

import requests

from .models import Video

_BASE = "https://www.googleapis.com/youtube/v3"
_TIMEOUT = 20


def parse_uploads_playlist_id(raw: dict) -> str:
    items = raw.get("items") or []
    if not items:
        raise LookupError("channel not found for handle")
    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def parse_videos(raw: dict, creator_name: str) -> list[Video]:
    videos = []
    for item in raw.get("items") or []:
        snippet = item["snippet"]
        videos.append(
            Video(
                video_id=snippet["resourceId"]["videoId"],
                title=snippet["title"],
                description=snippet["description"],
                published_at=snippet["publishedAt"],
                creator_name=creator_name,
            )
        )
    return videos


def fetch_latest_videos(
    api_key: str, handle: str, creator_name: str, limit: int = 5
) -> list[Video]:
    channels = requests.get(
        f"{_BASE}/channels",
        params={"part": "contentDetails", "forHandle": handle, "key": api_key},
        timeout=_TIMEOUT,
    )
    channels.raise_for_status()
    playlist_id = parse_uploads_playlist_id(channels.json())

    items = requests.get(
        f"{_BASE}/playlistItems",
        params={
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": str(limit),
            "key": api_key,
        },
        timeout=_TIMEOUT,
    )
    items.raise_for_status()
    return parse_videos(items.json(), creator_name)
