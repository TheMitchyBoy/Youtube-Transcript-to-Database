from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from ytdb.api.app import create_app
from ytdb.db.job_repository import SyncJobRepository
from ytdb.db.repository import TranscriptRepository
from ytdb.youtube.channel import ChannelInfo, VideoInfo
from ytdb.youtube.transcripts import TranscriptData


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    db_path = tmp_path / "api-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    return TestClient(create_app())


@pytest.fixture
def seeded_repository(tmp_path, monkeypatch):
    db_path = tmp_path / "seed.db"
    url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", url)
    repo = TranscriptRepository(url)
    repo.init_db()

    channel_info = ChannelInfo(
        channel_id="UCtestchannel00000001",
        name="Test Channel",
        url="https://www.youtube.com/@test",
    )
    video_info = VideoInfo(
        video_id="vid001",
        title="Hello World Video",
        published_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        url="https://www.youtube.com/watch?v=vid001",
    )
    transcript_data = TranscriptData("English", "en", False, "Hello world transcript text")

    with repo.session() as session:
        channel = repo.upsert_channel(session, channel_info)
        video = repo.upsert_video(session, channel, video_info)
        repo.upsert_transcript(session, video, transcript_data)
        SyncJobRepository().create_job(
            session,
            name="Daily",
            channel_account="@test",
            max_videos=10,
            languages=["en"],
            frequency="24h",
            enabled=True,
            force_refresh=False,
        )
        session.commit()

    return repo


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "ready" in body


def test_stats_endpoint(seeded_repository):
    client = TestClient(create_app())
    response = client.get("/api/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["channels"] == 1
    assert body["videos"] == 1
    assert body["transcripts"] == 1
    assert body["sync_jobs"] == 1


def test_list_transcripts_endpoint(seeded_repository):
    client = TestClient(create_app())
    response = client.get("/api/transcripts")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["video_title"] == "Hello World Video"
    assert "Hello world" in body[0]["preview"]


def test_search_transcripts_endpoint(seeded_repository):
    client = TestClient(create_app())
    response = client.get("/api/transcripts", params={"search": "hello world"})
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.get("/api/transcripts", params={"search": "missing"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_transcript_endpoint(seeded_repository):
    client = TestClient(create_app())
    listing = client.get("/api/transcripts").json()
    transcript_id = listing[0]["id"]

    response = client.get(f"/api/transcripts/{transcript_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Hello world transcript text"
    assert body["channel_name"] == "Test Channel"


def test_get_transcript_not_found(seeded_repository):
    client = TestClient(create_app())
    response = client.get("/api/transcripts/9999")
    assert response.status_code == 404


def test_repository_stats_and_search(seeded_repository):
    with seeded_repository.session() as session:
        stats = seeded_repository.get_stats(session)
        assert stats["transcripts"] == 1

        rows = seeded_repository.search_transcripts(session, search="Hello")
        assert len(rows) == 1

        row = seeded_repository.get_transcript(session, rows[0][0].id)
        assert row is not None
        assert row[0].content == "Hello world transcript text"
