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

## Backend Endpoints

- `GET /health`
- `GET /agents`
- `POST /pipeline/run`

## Build Path

1. Replace `frontend/src/data/rosewoodPipeline.js` with data from `POST /pipeline/run`.
2. Replace each backend stub in `backend/app/agents/` with real agent logic.
3. Add persistence for guest profiles, ambient signals, and generated letters.
4. Add Compositor output for LaTeX or print-ready PDF generation.
5. Add Audio Agent output for script generation and voice synthesis.
