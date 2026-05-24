# mayda-ai

> Voice AI assistant for restaurant ordering — take orders, answer questions, and handle reservations through natural speech.

## Overview

`mayda-ai` is a full-stack voice AI system that lets customers interact with restaurants conversationally. It transcribes speech, processes intent via LLM, and responds with voice — all in real time. Built for call center and in-store kiosk scenarios.

## Architecture

```
                    ┌─────────────┐
  Phone/SIP  ──────▶│   Twilio    │───▶  FastAPI Backend
                    └─────────────┘       │
                                          ├─▶ OpenAI (intent parsing)
                                          ├─▶ ElevenLabs (TTS)
                                          └─▶ Cartesia AI (voice)
                                    │
                              React Frontend (Vite)
```

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI (Python) |
| Frontend | React, TypeScript, Vite |
| Voice | ElevenLabs, Cartesia AI |
| AI | OpenAI GPT |
| Telephony | Twilio |
| Package | Poetry |

## Project Structure

```
mayda-ai/
├── backend/
│   ├── app/           # FastAPI routes, services, models
│   ├── docker/        # Docker configuration
│   └── Dockerfile
├── frontend/
│   ├── src/           # React components, pages, state
│   └── public/
├── pyproject.toml     # Python dependencies
└── poetry.lock
```

## Getting Started

```bash
# Backend
cd backend
poetry install
poetry run uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

Docker Compose is also available for running both services together.

## Features

- **Speech-to-speech ordering** — customer speaks, AI transcribes and understands
- **Menu-aware** — understands restaurant menu context for recommendations
- **Multi-intent handling** — orders, modifications, cancellations, inquiries
- **Real-time voice responses** — low-latency TTS pipeline
