"""In-memory parse jobs. Source page URL is kept only in process memory."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import DOWNLOAD_DIR


@dataclass
class Job:
    id: str
    page_url: str
    title: str
    ext: str
    filesize: int | None
    thumbnail: str | None
    extractor: str
    platform: str
    direct_url: str | None
    needs_merge: bool = False
    filepath: Path | None = None
    created_at: float = field(default_factory=time.time)
    extra: dict[str, Any] = field(default_factory=dict)


class JobStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, Job] = {}

    def create(self, **kwargs) -> Job:
        job_id = uuid.uuid4().hex
        job = Job(id=job_id, **kwargs)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def set_path(self, job_id: str, path: Path) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.filepath = path


STORE = JobStore()
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
