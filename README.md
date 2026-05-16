# The Rosewood Letter

A basic interactive skeleton for the hackathon concept: an invisible overnight AI
pipeline that produces one beautiful physical morning letter for a luxury hotel guest.

## What is included

- `index.html` — the first-screen dashboard and printed letter preview.
- `styles.css` — the soft dark green Rosewood-inspired visual system.
- `app.js` — a small pipeline simulation for the agent flow.

The current version is intentionally static and easy to iterate on. It gives the team a
usable artifact immediately while leaving clear seams for real data, agent outputs, audio,
QR generation, LaTeX composition, and print handoff.

## Core agent skeleton

1. Intent Agent
2. World Agent
3. Rhythm Agent
4. Discovery Agent
5. Temporal Resonance Layer
6. Voice Agent
7. Crossword Agent
8. Compositor Agent
9. Audio Agent

## Run locally

Open `index.html` in a browser.

For a local server:

```bash
python3 -m http.server 5173
```

Then visit `http://localhost:5173`.

## Suggested next build steps

- Replace the hard-coded Visit Intent Object with a JSON fixture.
- Add an `/agents` folder with one module per agent and shared schemas.
- Generate the morning letter from agent output instead of static copy.
- Add a real QR code target for the audio note.
- Add print CSS and a LaTeX export path for the Compositor Agent.
- Add a simple backend route for running the whole pipeline overnight.
