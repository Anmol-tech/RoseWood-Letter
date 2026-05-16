# Rosewood Letter Backend

FastAPI skeleton for the overnight multi-agent pipeline.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Provider keys

The pipeline works without provider keys by using deterministic demo fallbacks.
Set these environment variables to enable live agents:

```bash
cp ../.env.example ../.env
export ANTHROPIC_API_KEY="..."
export ANTHROPIC_MODEL="claude-sonnet-4-5"

export ELEVENLABS_API_KEY="..."
export ELEVENLABS_DEFAULT_VOICE_ID="..."
```

Optional per-intent voices:

```bash
export ELEVENLABS_VOICE_ID_QUIET_RESTORATION="..."
export ELEVENLABS_VOICE_ID_MILESTONE="..."
export ELEVENLABS_VOICE_ID_CELEBRATION_DISCOVERY="..."
```

Generated voice notes are saved under `app/static/audio/` and served from
`/static/audio/{file}.mp3`.

## Endpoints

- `GET /health`
- `GET /agents`
- `GET /scenarios`
- `POST /profiles`
- `GET /profiles`
- `GET /profiles/{profile_id}`
- `POST /pipeline/run`

Customer profiles and personas are stored in SQLite at
`backend/data/rosewood.sqlite`. The database is created automatically on startup.
Use `profile_id` in `POST /pipeline/run` to generate a letter from a stored
profile, or pass an inline `profile` for an ad hoc run.

`GET /scenarios` returns three ready-made demo payloads:

- `quiet-restoration`
- `milestone-couple`
- `celebration-discovery`

## Where to build next

- `app/schemas.py` defines the shared API contract.
- `app/db.py` owns SQLite profile/persona persistence.
- `app/pipeline.py` orchestrates the agents.
- `app/agents/` contains one replaceable class per agent.
