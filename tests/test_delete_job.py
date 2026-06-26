from sqlalchemy import select

from ytdb.db.job_repository import SyncJobRepository
from ytdb.db.models import SyncRun
from ytdb.db.repository import TranscriptRepository


def test_delete_job_with_runs():
    repo = TranscriptRepository("sqlite+pysqlite:///:memory:")
    repo.init_db()
    job_repo = SyncJobRepository()

    with repo.session() as session:
        job = job_repo.create_job(
            session,
            name="delete me",
            channel_account="@test",
            max_videos=5,
            languages=["en"],
            frequency="manual",
            enabled=True,
            force_refresh=False,
        )
        run = job_repo.mark_running(session, job)
        job_repo.complete_run(
            session,
            job,
            run,
            status="success",
            videos_processed=1,
            transcripts_saved=1,
            transcripts_skipped=0,
            errors=0,
        )
        session.commit()
        job_id = job.id

    with repo.session() as session:
        job = job_repo.get_job(session, job_id)
        assert job is not None
        job_repo.delete_job(session, job)
        session.commit()
        assert job_repo.get_job(session, job_id) is None
        assert session.scalars(select(SyncRun)).all() == []
