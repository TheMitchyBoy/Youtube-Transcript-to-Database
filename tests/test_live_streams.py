from unittest.mock import MagicMock, patch

import pytest

from ytdb.sync import SyncService
from ytdb.youtube.channel import ChannelInfo, VideoInfo


@pytest.fixture
def repository():
    from ytdb.db.repository import TranscriptRepository

    repo = TranscriptRepository("sqlite+pysqlite:///:memory:")
    repo.init_db()
    return repo


def test_list_content_dedupes_live_and_stream(repository):
    channel_client = MagicMock()
    channel_client.get_channel_info.return_value = ChannelInfo(
        "UCchannel", "Channel", "https://youtube.com/@channel"
    )
    channel_client.list_content.return_value = [
        VideoInfo("live1", "Live now", None, "https://youtube.com/watch?v=live1", "live", True),
        VideoInfo("stream1", "Past stream", None, "https://youtube.com/watch?v=stream1", "stream", False),
    ]

    transcript_client = MagicMock()
    transcript_client.fetch_transcript.return_value = MagicMock(
        language="English",
        language_code="en",
        is_auto_generated=True,
        content="hello",
    )

    service = SyncService(
        repository=repository,
        channel_client=channel_client,
        transcript_client=transcript_client,
    )

    result = service.sync_channel(
        "@channel",
        include_videos=False,
        include_streams=True,
        include_live=True,
    )

    assert result.videos_processed == 2
    assert result.transcripts_saved == 2
    channel_client.list_content.assert_called_once_with(
        "@channel",
        max_items=None,
        include_videos=False,
        include_streams=True,
        include_live=True,
    )


def test_live_stream_is_not_skipped_when_transcript_exists(repository):
    channel_client = MagicMock()
    channel_client.get_channel_info.return_value = ChannelInfo(
        "UCchannel", "Channel", "https://youtube.com/@channel"
    )
    channel_client.list_content.return_value = [
        VideoInfo("live1", "Live now", None, "https://youtube.com/watch?v=live1", "live", True),
    ]

    transcript_client = MagicMock()
    transcript_client.fetch_transcript.side_effect = [
        type("T", (), {
            "language": "English",
            "language_code": "en",
            "is_auto_generated": True,
            "content": "part one",
        })(),
        type("T", (), {
            "language": "English",
            "language_code": "en",
            "is_auto_generated": True,
            "content": "part one updated",
        })(),
    ]

    service = SyncService(
        repository=repository,
        channel_client=channel_client,
        transcript_client=transcript_client,
    )

    first = service.sync_channel("@channel", skip_existing=True)
    second = service.sync_channel("@channel", skip_existing=True)

    assert first.transcripts_saved == 1
    assert second.transcripts_saved == 1
    assert transcript_client.fetch_transcript.call_count == 2


def test_channel_client_merge_prioritizes_live():
    from ytdb.youtube.channel import ChannelClient

    client = ChannelClient()
    same_id = VideoInfo(
        "abc123",
        "Title",
        None,
        "https://youtube.com/watch?v=abc123",
        "video",
        False,
    )
    live_id = VideoInfo(
        "abc123",
        "Title live",
        None,
        "https://youtube.com/watch?v=abc123",
        "live",
        True,
    )

    with patch.object(client, "get_current_live", return_value=None), patch.object(
        client, "_list_tab", side_effect=[[same_id], []]
    ):
        results = client.list_content(
            "@channel",
            include_videos=True,
            include_streams=False,
            include_live=False,
        )

    assert len(results) == 1
    assert results[0].content_type == "video"

    with patch.object(client, "get_current_live", return_value=live_id), patch.object(
        client, "_list_tab", side_effect=[[same_id], []]
    ):
        results = client.list_content(
            "@channel",
            include_videos=True,
            include_streams=False,
            include_live=True,
        )

    assert len(results) == 1
    assert results[0].is_live is True
    assert results[0].content_type == "live"
