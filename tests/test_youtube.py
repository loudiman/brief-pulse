"""Parsing YouTube API responses. Fixture mirrors the real playlistItems.list shape."""

import json
from pathlib import Path

from briefpulse.youtube import parse_uploads_playlist_id, parse_videos

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_videos_from_playlist_items() -> None:
    raw = json.loads((FIXTURES / "playlist_items.json").read_text(encoding="utf-8"))
    videos = parse_videos(raw, creator_name="Pokimane")
    assert len(videos) == 2
    v = videos[0]
    assert v.video_id == "dQw4w9WgXcQ"
    assert v.title == "my morning routine"
    assert "serum" in v.description
    assert v.published_at == "2026-08-10T09:00:00Z"
    assert v.creator_name == "Pokimane"


def test_parse_uploads_playlist_id_from_channels_response() -> None:
    raw = json.loads((FIXTURES / "channels.json").read_text(encoding="utf-8"))
    assert parse_uploads_playlist_id(raw) == "UUq-Fj5jknLsUf-MWSy4_brA"


def test_missing_items_returns_empty_list() -> None:
    assert parse_videos({"items": []}, creator_name="x") == []
