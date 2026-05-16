# Rosewood Letter Backend

FastAPI skeleton for the overnight multi-agent pipeline.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
- `GET /agents`
- `POST /pipeline/run`

## Where to build next

- `app/schemas.py` defines the shared API contract.
- `app/pipeline.py` orchestrates the agents.
- `app/agents/` contains one replaceable class per agent.
