# The Rosewood Letter

A full-stack prototype for the hackathon concept: an invisible overnight AI pipeline
that produces one beautiful physical morning letter for a luxury hotel guest.

## Project Structure

```text
frontend/   Vite + React operator dashboard and letter preview
backend/    FastAPI skeleton for the multi-agent pipeline
```

## Frontend

```bash
cd frontend
npm run dev
```

Vite usually serves the app at `http://localhost:5173`.

## Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

FastAPI docs will be available at `http://localhost:8000/docs`.

Provider-backed agents are enabled with environment variables:

```bash
cp .env.example .env
export ANTHROPIC_API_KEY="..."
export ELEVENLABS_API_KEY="..."
export ELEVENLABS_DEFAULT_VOICE_ID="..."
```

Without keys, the backend uses deterministic demo fallbacks.

## Backend Endpoints

- `GET /health`
- `GET /provider-status`
- `GET /agents`
- `GET /scenarios`
- `POST /profiles`
- `GET /profiles`
- `GET /profiles/{profile_id}`
- `POST /pipeline/run`

`POST /pipeline/run` accepts either an inline `profile` or a stored `profile_id`.
Stored customer profiles and personas are saved in SQLite at
`backend/data/rosewood.sqlite` when the backend starts or profile APIs are used.

The demo scenarios are:

- `quiet-restoration`: solo, private, decision-light stay.
- `milestone-couple`: first trip together in two years with an evening centerpiece.
- `celebration-discovery`: birthday/discovery guest looking for hidden local access.

## Build Path

1. Replace the remaining static frontend fixture fields with data from `POST /pipeline/run`.
2. Replace each backend stub in `backend/app/agents/` with real agent logic.
3. Persist ambient signals and generated letter artifacts.
4. Add Compositor output for LaTeX or print-ready PDF generation.
5. Add Audio Agent output for script generation and voice synthesis.
