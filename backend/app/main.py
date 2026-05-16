from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.pipeline import pipeline
from app.schemas import PipelineRequest, PipelineResponse

app = FastAPI(
    title="Rosewood Letter API",
    version="0.1.0",
    description="Backend skeleton for the overnight multi-agent Rosewood Letter pipeline.",
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
            "Temporal Resonance Layer",
            "Voice Agent",
            "Crossword Agent",
            "Compositor Agent",
            "Audio Agent",
        ]
    }


@app.post("/pipeline/run", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return pipeline.run(request)
