import json
from datetime import datetime
from uuid import uuid4

from app.db import get_connection, init_db
from app.schemas import DeliveryArtifact, PipelineJobBatchState, PipelineJobState, PipelineRequest, PipelineResponse

DEMO_EMAIL = "asharma14@scu.edu"


class PipelineJobStore:
    def __init__(self) -> None:
        self._active_requests: dict[str, dict[str, PipelineRequest]] = {}

    def init_tables(self) -> None:
        init_db()
        with get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_batches (
                    batch_id TEXT PRIMARY KEY,
                    max_concurrency INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS pipeline_jobs (
                    job_id TEXT PRIMARY KEY,
                    batch_id TEXT NOT NULL,
                    job_index INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    guest_name TEXT NOT NULL,
                    suite TEXT NOT NULL,
                    location TEXT NOT NULL DEFAULT 'Rosewood Property',
                    request_json TEXT NOT NULL,
                    current_agents_json TEXT NOT NULL,
                    completed_agents_json TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    response_json TEXT,
                    delivery_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(batch_id) REFERENCES pipeline_batches(batch_id)
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(pipeline_jobs)").fetchall()
            }
            if "location" not in columns:
                connection.execute(
                    """
                    ALTER TABLE pipeline_jobs
                    ADD COLUMN location TEXT NOT NULL DEFAULT 'Rosewood Property'
                    """
                )
            if "delivery_json" not in columns:
                connection.execute("ALTER TABLE pipeline_jobs ADD COLUMN delivery_json TEXT")

    def recover_interrupted_jobs(self) -> None:
        self.init_tables()
        now = datetime.utcnow().isoformat()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE pipeline_jobs
                SET status = 'failed',
                    current_agents_json = '[]',
                    progress = 100,
                    error = COALESCE(error, 'Server restarted before this job completed.'),
                    updated_at = ?
                WHERE status IN ('queued', 'running')
                """,
                (now,),
            )

    def create_batch(
        self,
        *,
        requests: list[PipelineRequest],
        max_concurrency: int,
    ) -> PipelineJobBatchState:
        self.init_tables()
        now = datetime.utcnow()
        batch_id = uuid4().hex
        jobs = []

        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO pipeline_batches (batch_id, max_concurrency, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (batch_id, max_concurrency, now.isoformat(), now.isoformat()),
            )

            request_map = {}

            for index, request in enumerate(requests):
                location = self._location_from_request(request)
                job = PipelineJobState(
                    job_id=uuid4().hex,
                    batch_id=batch_id,
                    index=index,
                    status="queued",
                    guest_name=request.profile.guest_name,
                    suite=request.profile.suite,
                    location=location,
                    created_at=now,
                    updated_at=now,
                )
                request.artifact_id = job.job_id
                jobs.append(job)
                request_map[job.job_id] = request
                connection.execute(
                    """
                    INSERT INTO pipeline_jobs (
                        job_id,
                        batch_id,
                        job_index,
                        status,
                        guest_name,
                        suite,
                        location,
                        request_json,
                        current_agents_json,
                        completed_agents_json,
                        progress,
                        response_json,
                        delivery_json,
                        error,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.job_id,
                        batch_id,
                        index,
                        job.status,
                        job.guest_name,
                        job.suite,
                        job.location,
                        request.model_dump_json(),
                        json.dumps(job.current_agents),
                        json.dumps(job.completed_agents),
                        job.progress,
                        None,
                        job.delivery.model_dump_json(),
                        None,
                        now.isoformat(),
                        now.isoformat(),
                    ),
                )

        self._active_requests[batch_id] = request_map
        return self.get_batch(batch_id)

    def list_batches(self) -> list[PipelineJobBatchState]:
        self.init_tables()
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT batch_id
                FROM pipeline_batches
                ORDER BY updated_at DESC
                """
            ).fetchall()

        return [
            state
            for row in rows
            if (state := self.get_batch(row["batch_id"])) is not None
        ]

    def list_jobs(self) -> list[PipelineJobState]:
        self.init_tables()
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pipeline_jobs
                ORDER BY created_at DESC, job_index ASC
                """
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def get_job_by_id(self, job_id: str) -> PipelineJobState | None:
        self.init_tables()
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM pipeline_jobs
                WHERE job_id = ?
                """,
                (job_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_job(row)

    def _row_to_job(self, row) -> PipelineJobState:
        response = None
        if row["response_json"]:
            response = PipelineResponse.model_validate(json.loads(row["response_json"]))
        delivery = DeliveryArtifact()
        if row["delivery_json"]:
            delivery = DeliveryArtifact.model_validate(json.loads(row["delivery_json"]))
        if response is not None:
            delivery.letter_url = delivery.letter_url or response.delivery.letter_url or response.print_artifact.qr_url
            delivery.email.to = delivery.email.to or response.profile.email or DEMO_EMAIL

        return PipelineJobState(
            job_id=row["job_id"],
            batch_id=row["batch_id"],
            index=row["job_index"],
            status=row["status"],
            guest_name=row["guest_name"],
            suite=row["suite"],
            location=row["location"],
            current_agents=json.loads(row["current_agents_json"]),
            completed_agents=json.loads(row["completed_agents_json"]),
            progress=row["progress"],
            response=response,
            delivery=delivery,
            error=row["error"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def _get_jobs(self, batch_id: str) -> list[PipelineJobState]:
        self.init_tables()
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM pipeline_jobs
                WHERE batch_id = ?
                ORDER BY job_index ASC
                """,
                (batch_id,),
            ).fetchall()

        return [self._row_to_job(row) for row in rows]

    def _get_max_concurrency(self, batch_id: str) -> int | None:
        self.init_tables()
        with get_connection() as connection:
            row = connection.execute(
                "SELECT max_concurrency FROM pipeline_batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()

        if row is None:
            return None

        return row["max_concurrency"]

    def _persist_job(self, job: PipelineJobState) -> None:
        now = job.updated_at
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE pipeline_jobs
                SET status = ?,
                    current_agents_json = ?,
                    completed_agents_json = ?,
                    progress = ?,
                    response_json = ?,
                    delivery_json = ?,
                    error = ?,
                    updated_at = ?
                WHERE job_id = ? AND batch_id = ?
                """,
                (
                    job.status,
                    json.dumps(job.current_agents),
                    json.dumps(job.completed_agents),
                    job.progress,
                    job.response.model_dump_json() if job.response else None,
                    job.delivery.model_dump_json(),
                    job.error,
                    now.isoformat(),
                    job.job_id,
                    job.batch_id,
                ),
            )
            connection.execute(
                "UPDATE pipeline_batches SET updated_at = ? WHERE batch_id = ?",
                (now.isoformat(), job.batch_id),
            )

    def _request_from_db(self, batch_id: str, job_id: str) -> PipelineRequest | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT request_json
                FROM pipeline_jobs
                WHERE batch_id = ? AND job_id = ?
                """,
                (batch_id, job_id),
            ).fetchone()

        if row is None:
            return None

        return PipelineRequest.model_validate(json.loads(row["request_json"]))

    def _location_from_request(self, request: PipelineRequest) -> str:
        if request.profile.property_location:
            return request.profile.property_location

        notes = request.profile.booking_notes
        if ":" in notes:
            return notes.split(":", 1)[0].strip() or "Rosewood Property"

        return "Rosewood Property"

    def get_batch(self, batch_id: str) -> PipelineJobBatchState | None:
        max_concurrency = self._get_max_concurrency(batch_id)
        if max_concurrency is None:
            return None

        jobs = self._get_jobs(batch_id)
        return PipelineJobBatchState(
            batch_id=batch_id,
            total=len(jobs),
            completed=sum(1 for job in jobs if job.status == "completed"),
            failed=sum(1 for job in jobs if job.status == "failed"),
            running=sum(1 for job in jobs if job.status == "running"),
            queued=sum(1 for job in jobs if job.status == "queued"),
            max_concurrency=max_concurrency,
            jobs=jobs,
        )

    def get_request(self, batch_id: str, job_id: str) -> PipelineRequest | None:
        request = self._active_requests.get(batch_id, {}).get(job_id)
        if request is not None:
            return request

        return self._request_from_db(batch_id, job_id)

    def get_job(self, batch_id: str, job_id: str) -> PipelineJobState | None:
        return next((job for job in self._get_jobs(batch_id) if job.job_id == job_id), None)

    def update_job(self, batch_id: str, job_id: str, **changes) -> PipelineJobState | None:
        job = self.get_job(batch_id, job_id)
        if job is None:
            return None

        updated = job.model_copy(update={**changes, "updated_at": datetime.utcnow()})
        self._persist_job(updated)
        return updated

    def mark_completed(
        self,
        *,
        batch_id: str,
        job_id: str,
        response: PipelineResponse,
    ) -> None:
        completed_agents = [output.agent for output in response.outputs]
        self.update_job(
            batch_id,
            job_id,
            status="completed",
            current_agents=[],
            completed_agents=completed_agents,
            progress=100,
            response=response,
            delivery=response.delivery,
            error=None,
        )

    def update_delivery(
        self,
        *,
        job_id: str,
        delivery: DeliveryArtifact,
        response: PipelineResponse | None = None,
    ) -> PipelineJobState | None:
        job = self.get_job_by_id(job_id)
        if job is None:
            return None

        updated_response = response or job.response
        if updated_response is not None:
            updated_response = updated_response.model_copy(update={"delivery": delivery})

        updated = job.model_copy(
            update={
                "delivery": delivery,
                "response": updated_response,
                "updated_at": datetime.utcnow(),
            }
        )
        self._persist_job(updated)
        return updated

    def mark_failed(self, *, batch_id: str, job_id: str, error: str) -> None:
        self.update_job(
            batch_id,
            job_id,
            status="failed",
            current_agents=[],
            progress=100,
            error=error,
        )


job_store = PipelineJobStore()
