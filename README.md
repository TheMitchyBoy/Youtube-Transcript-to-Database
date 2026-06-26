# YouTube Transcript to Database

Fetch transcripts from every video on a selected YouTube channel and store them in PostgreSQL.

## Features

- Accept a channel by URL, `@handle`, or channel ID (`UC...`)
- Discover all videos on the channel via `yt-dlp` (no YouTube API key required)
- Download captions with `youtube-transcript-api` (manual or auto-generated)
- Persist channels, videos, and transcripts in PostgreSQL
- Skip videos that already have transcripts unless `--force` is used
- Idempotent upserts — safe to re-run

## Quick start

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

### 3. Initialize the database

```bash
ytdb init-db
```

### 4. Sync a channel

```bash
# By @handle
ytdb sync @mkbhd --max-videos 10

# By channel URL
ytdb sync "https://www.youtube.com/@mkbhd" --language en

# Re-fetch existing transcripts
ytdb sync @mkbhd --force
```

### 5. List synced channels

```bash
ytdb list-channels
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://ytdb:ytdb@localhost:5432/ytdb` |
| `YOUTUBE_API_KEY` | Optional; not required for core sync | — |

## Database schema

- **channels** — YouTube channel metadata
- **videos** — Videos belonging to a channel
- **transcripts** — Full transcript text per video and language

Example query:

```sql
SELECT c.name, v.title, t.language_code, LEFT(t.content, 120) AS preview
FROM transcripts t
JOIN videos v ON v.id = t.video_id
JOIN channels c ON c.id = v.channel_id
ORDER BY t.fetched_at DESC
LIMIT 20;
```

## CLI reference

```
ytdb init-db
ytdb list-channels
ytdb sync ACCOUNT [--max-videos N] [--language CODE]... [--force]
```

`ACCOUNT` can be:

- `https://www.youtube.com/@handle`
- `@handle` or `handle`
- `UCxxxxxxxxxxxxxxxxxxxxxx` (24-character channel ID)

## Development

```bash
pip install -e .
pip install pytest
pytest
```

## Limitations

- Only videos with available captions are stored (many channels disable captions on some uploads).
- YouTube may rate-limit heavy usage; use `--max-videos` while testing.
- Transcript availability depends on the uploader and YouTube's caption settings.

## License

MIT
