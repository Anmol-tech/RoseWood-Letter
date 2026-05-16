from contextlib import asynccontextmanager
import asyncio
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.db import create_guest_profile, get_guest_profile, init_db, list_guest_profiles
from app.job_store import job_store
from app.pipeline import pipeline
from app.scenarios import DEMO_SCENARIOS
from app.services import anthropic_client, delivery_service, elevenlabs_client
from app.schemas import (
    DeliveryChannelState,
    DemoScenario,
    DeliveryRequest,
    GuestReservationRequest,
    GuestReservationResponse,
    GuestProfileCreate,
    GuestProfileRecord,
    PipelineBatchRequest,
    PipelineBatchResponse,
    PipelineBatchResult,
    PipelineJobBatchState,
    PipelineJobStartRequest,
    PipelineJobState,
    PipelineRequest,
    PipelineResponse,
)

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    job_store.recover_interrupted_jobs()
    yield


app = FastAPI(
    title="Rosewood Letter API",
    version="0.1.0",
    description="Backend skeleton for the overnight multi-agent Rosewood Letter pipeline.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/provider-status")
def provider_status() -> dict:
    return {
        "anthropic": anthropic_client.status(),
        "elevenlabs": elevenlabs_client.status(),
        "delivery": delivery_service.status(),
    }


@app.get("/elevenlabs/voices")
async def elevenlabs_voices() -> dict[str, list[dict[str, str]]]:
    return {"voices": await elevenlabs_client.list_voices()}


@app.get("/agents")
def list_agents() -> dict[str, list[str]]:
    return {
        "agents": [
            "Intent Agent",
            "World Agent",
            "Rhythm Agent",
            "Discovery Agent",
            "Memory Agent",
            "Temporal Resonance Layer",
            "Voice Agent",
            "Crossword Agent",
            "Compositor Agent",
            "Audio Agent",
        ]
    }


@app.get("/scenarios", response_model=list[DemoScenario])
def scenarios() -> list[DemoScenario]:
    return DEMO_SCENARIOS


@app.post("/profiles", response_model=GuestProfileRecord)
def create_profile(profile: GuestProfileCreate) -> GuestProfileRecord:
    return create_guest_profile(profile)


@app.get("/profiles", response_model=list[GuestProfileRecord])
def profiles() -> list[GuestProfileRecord]:
    return list_guest_profiles()


@app.get("/profiles/{profile_id}", response_model=GuestProfileRecord)
def profile(profile_id: int) -> GuestProfileRecord:
    stored_profile = get_guest_profile(profile_id)
    if stored_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return stored_profile


def resolve_profile(request: PipelineRequest) -> PipelineRequest:
    if request.profile_id is not None:
        stored_profile = get_guest_profile(request.profile_id)
        if stored_profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        request.profile = stored_profile

    return request


def attach_public_context(pipeline_request: PipelineRequest, http_request: Request) -> PipelineRequest:
    if pipeline_request.public_base_url is None:
        pipeline_request.public_base_url = str(http_request.base_url).rstrip("/")
    if pipeline_request.frontend_base_url is None:
        pipeline_request.frontend_base_url = (
            os.getenv("FRONTEND_BASE_URL")
            or http_request.headers.get("origin")
            or "http://localhost:5173"
        ).rstrip("/")

    return pipeline_request


@app.post("/pipeline/run", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest, http_request: Request) -> PipelineResponse:
    request = attach_public_context(resolve_profile(request), http_request)
    return await pipeline.arun(request)


@app.post("/pipeline/run-batch", response_model=PipelineBatchResponse)
async def run_pipeline_batch(batch: PipelineBatchRequest, http_request: Request) -> PipelineBatchResponse:
    semaphore = asyncio.Semaphore(batch.max_concurrency)

    async def run_one(index: int, request: PipelineRequest) -> PipelineBatchResult:
        async with semaphore:
            try:
                resolved = attach_public_context(resolve_profile(request), http_request)
                response = await pipeline.arun(resolved)
                return PipelineBatchResult(
                    index=index,
                    profile_id=resolved.profile_id or resolved.profile.id,
                    guest_name=response.profile.guest_name,
                    suite=response.profile.suite,
                    status="completed",
                    response=response,
                )
            except HTTPException as error:
                return PipelineBatchResult(
                    index=index,
                    profile_id=request.profile_id,
                    guest_name=request.profile.guest_name,
                    suite=request.profile.suite,
                    status="failed",
                    error=str(error.detail),
                )
            except Exception as error:
                return PipelineBatchResult(
                    index=index,
                    profile_id=request.profile_id,
                    guest_name=request.profile.guest_name,
                    suite=request.profile.suite,
                    status="failed",
                    error=str(error),
                )

    results = await asyncio.gather(
        *[run_one(index, request) for index, request in enumerate(batch.requests)]
    )
    completed = sum(1 for result in results if result.status == "completed")

    return PipelineBatchResponse(
        total=len(results),
        completed=completed,
        failed=len(results) - completed,
        max_concurrency=batch.max_concurrency,
        results=results,
    )


@app.post("/pipeline/jobs", response_model=PipelineJobBatchState)
async def start_pipeline_jobs(batch: PipelineJobStartRequest, http_request: Request) -> PipelineJobBatchState:
    resolved_requests = [
        attach_public_context(resolve_profile(request), http_request)
        for request in batch.requests
    ]
    state = job_store.create_batch(
        requests=resolved_requests,
        max_concurrency=batch.max_concurrency,
    )
    asyncio.create_task(run_job_batch(state.batch_id))
    return state


@app.get("/pipeline/jobs", response_model=list[PipelineJobBatchState])
def list_pipeline_jobs() -> list[PipelineJobBatchState]:
    return job_store.list_batches()


@app.get("/pipeline/job-history", response_model=list[PipelineJobState])
def list_pipeline_job_history() -> list[PipelineJobState]:
    return job_store.list_jobs()


@app.get("/pipeline/job-history/{job_id}", response_model=PipelineJobState)
def get_pipeline_job_history_item(job_id: str) -> PipelineJobState:
    job = job_store.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    return job


@app.post("/pipeline/job-history/{job_id}/deliver", response_model=PipelineJobState)
async def deliver_pipeline_job(job_id: str, request: DeliveryRequest) -> PipelineJobState:
    job = job_store.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Pipeline job not found")
    if job.status != "completed" or job.response is None:
        raise HTTPException(status_code=409, detail="Pipeline job is not completed yet")

    email_result = None
    if request.email:
        email_to = request.email_to or job.response.profile.email
        if not email_to:
            raise HTTPException(status_code=400, detail="Email recipient is missing")
        email_result = await delivery_service.send_email(job=job, to_email=email_to)

    delivery = delivery_service.merge_delivery(
        job=job,
        email=email_result,
    )
    updated = job_store.update_delivery(job_id=job_id, delivery=delivery)
    if updated is None:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    return updated


@app.post("/guest-reservations", response_model=GuestReservationResponse)
async def create_guest_reservation(request: GuestReservationRequest) -> GuestReservationResponse:
    job = job_store.get_job_by_id(request.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Pipeline job not found")
    if job.status != "completed" or job.response is None:
        raise HTTPException(status_code=409, detail="Pipeline job is not completed yet")
    if not request.options:
        raise HTTPException(status_code=400, detail="Reservation options are missing")

    email_to = request.email_to or job.response.profile.email or job.delivery.email.to

    if not email_to:
        # No email address — record the reservation without delivery.
        return GuestReservationResponse(
            status="recorded",
            message="Reservation request recorded. No email address on file — Rosewood will follow up directly.",
            email=DeliveryChannelState(
                status="skipped",
                provider="none",
                error="No guest email address available.",
            ),
        )

    email = await delivery_service.send_reservation_email(
        job=job,
        to_email=email_to,
        options=request.options,
    )
    status = "sent" if email.status == "sent" else email.status
    return GuestReservationResponse(
        status=status,
        message=(
            "Reservation request sent to Rosewood."
            if email.status == "sent"
            else "Reservation request was recorded, but email delivery needs attention."
        ),
        email=email,
    )


@app.get("/pipeline/jobs/{batch_id}", response_model=PipelineJobBatchState)
def get_pipeline_jobs(batch_id: str) -> PipelineJobBatchState:
    state = job_store.get_batch(batch_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Pipeline batch not found")

    return state


@app.get("/pipeline/jobs/{batch_id}/{job_id}", response_model=PipelineJobState)
def get_pipeline_job(batch_id: str, job_id: str) -> PipelineJobState:
    job = job_store.get_job(batch_id, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Pipeline job not found")

    return job


async def run_job_batch(batch_id: str) -> None:
    state = job_store.get_batch(batch_id)
    if state is None:
        return

    semaphore = asyncio.Semaphore(state.max_concurrency)

    async def run_one(job: PipelineJobState) -> None:
        async with semaphore:
            request = job_store.get_request(batch_id, job.job_id)
            if request is None:
                job_store.mark_failed(
                    batch_id=batch_id,
                    job_id=job.job_id,
                    error="Pipeline request not found.",
                )
                return

            job_store.update_job(
                batch_id,
                job.job_id,
                status="running",
                current_agents=["Queued for Intent Agent"],
                progress=2,
            )

            async def progress_callback(event: dict) -> None:
                current = job_store.get_job(batch_id, job.job_id)
                if current is None:
                    return

                agent = event["agent"]
                current_agents = list(current.current_agents)
                completed_agents = list(current.completed_agents)

                if event["event"] == "started" and agent not in current_agents:
                    current_agents.append(agent)
                if event["event"] == "completed":
                    current_agents = [item for item in current_agents if item != agent]
                    if agent not in completed_agents:
                        completed_agents.append(agent)

                job_store.update_job(
                    batch_id,
                    job.job_id,
                    current_agents=current_agents,
                    completed_agents=completed_agents,
                    progress=max(current.progress, event["progress"]),
                )

            try:
                response = await pipeline.arun(request, progress_callback=progress_callback)
                job_store.mark_completed(
                    batch_id=batch_id,
                    job_id=job.job_id,
                    response=response,
                )
            except Exception as error:
                job_store.mark_failed(
                    batch_id=batch_id,
                    job_id=job.job_id,
                    error=str(error),
                )

    await asyncio.gather(*[run_one(job) for job in state.jobs])
