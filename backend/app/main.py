from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import create_guest_profile, get_guest_profile, init_db, list_guest_profiles
from app.pipeline import pipeline
from app.scenarios import DEMO_SCENARIOS
from app.schemas import (
    DemoScenario,
    GuestProfileCreate,
    GuestProfileRecord,
    PipelineRequest,
    PipelineResponse,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


@app.post("/pipeline/run", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    if request.profile_id is not None:
        stored_profile = get_guest_profile(request.profile_id)
        if stored_profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        request.profile = stored_profile

    return pipeline.run(request)
