from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import yt_dlp


CHANNEL_ID_PATTERN = re.compile(
    r"(?:youtube\.com/channel/|youtu\.be/channel/)([A-Za-z0-9_-]+)"
)
HANDLE_PATTERN = re.compile(r"youtube\.com/@([A-Za-z0-9._-]+)")
LEGACY_USER_PATTERN = re.compile(r"youtube\.com/(?:c|user)/([A-Za-z0-9._-]+)")


@dataclass(frozen=True)
class ChannelInfo:
    channel_id: str
    name: str | None
    url: str


@dataclass(frozen=True)
class VideoInfo:
    video_id: str
    title: str | None
    published_at: datetime | None
    url: str


def normalize_channel_url(account: str) -> str:
    account = account.strip()
    if account.startswith("http://") or account.startswith("https://"):
        return account.rstrip("/")

    if account.startswith("UC") and len(account) == 24:
        return f"https://www.youtube.com/channel/{account}"

    if account.startswith("@"):
        return f"https://www.youtube.com/{account}"

    return f"https://www.youtube.com/@{account}"


class ChannelClient:
    def __init__(self) -> None:
        self._ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }

    def get_channel_info(self, account: str) -> ChannelInfo:
        url = normalize_channel_url(account)
        with yt_dlp.YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        channel_id = info.get("channel_id") or info.get("id")
        if not channel_id:
            raise ValueError(f"Could not resolve channel ID from: {account}")

        return ChannelInfo(
            channel_id=channel_id,
            name=info.get("channel") or info.get("uploader") or info.get("title"),
            url=info.get("channel_url") or info.get("webpage_url") or url,
        )

    def list_videos(self, account: str, max_videos: int | None = None) -> list[VideoInfo]:
        url = normalize_channel_url(account)
        videos_url = f"{url}/videos"

        opts = {
            **self._ydl_opts,
            "playlistend": max_videos,
        }

        with yt_dlp.YoutubeDL(opts) as ydl:
            playlist = ydl.extract_info(videos_url, download=False)

        entries = playlist.get("entries") or []
        videos: list[VideoInfo] = []

        for entry in entries:
            if not entry:
                continue
            video = self._entry_to_video(entry)
            if video:
                videos.append(video)

        return videos

    def _entry_to_video(self, entry: dict[str, Any]) -> VideoInfo | None:
        video_id = entry.get("id")
        if not video_id or video_id.startswith("UC"):
            return None

        published_at = self._parse_timestamp(entry.get("timestamp") or entry.get("release_timestamp"))
        url = entry.get("url") or entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"

        return VideoInfo(
            video_id=video_id,
            title=entry.get("title"),
            published_at=published_at,
            url=url,
        )

    @staticmethod
    def _parse_timestamp(value: int | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromtimestamp(value, tz=timezone.utc)
