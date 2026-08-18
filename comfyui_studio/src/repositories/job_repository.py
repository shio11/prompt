"""生成ジョブ履歴をSQLiteに永続化するリポジトリ。"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from models.enums import JobKind, JobStatus, MediaType
from models.generation import GenerationJob


class JobRepository:
    """GenerationJobのCRUDのみを担当するリポジトリ。"""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def save(self, job: GenerationJob) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (id, kind, media_type, status, created_at, output_paths, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    output_paths=excluded.output_paths,
                    error_message=excluded.error_message
                """,
                (
                    job.id,
                    job.kind.value,
                    job.media_type.value,
                    job.status.value,
                    job.created_at.isoformat(),
                    json.dumps(job.output_paths),
                    job.error_message,
                ),
            )

    def find_by_id(self, job_id: str) -> Optional[GenerationJob]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def list_recent(self, limit: int = 20) -> List[GenerationJob]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    output_paths TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )

    @staticmethod
    def _row_to_job(row: Tuple) -> GenerationJob:
        job_id, kind, media_type, status, created_at, output_paths, error_message = row
        return GenerationJob(
            kind=JobKind(kind),
            media_type=MediaType(media_type),
            id=job_id,
            status=JobStatus(status),
            created_at=datetime.fromisoformat(created_at),
            output_paths=json.loads(output_paths),
            error_message=error_message,
        )
