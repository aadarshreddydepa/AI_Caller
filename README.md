# AI Caller — Local Voice Prototype

AI Caller is a multi-tenant business receptionist prototype. A business owner can configure approved services and FAQs, then test a browser-based voice conversation with a local AI agent. Calls, transcripts, leads, and owner callback requests are stored in PostgreSQL.

## Local architecture

```text
Browser microphone
  -> browser speech recognition
  -> Next.js dashboard
  -> Django API
  -> PostgreSQL / Redis (Docker)
  -> native Ollama (local conversation model)
  -> browser speech synthesis
```

The browser handles microphone transcription and spoken playback. Ollama runs natively on macOS for low-latency Apple Silicon/Metal performance. Docker is used only for PostgreSQL and Redis in this local prototype.

## Technology

- Next.js 16 + React 19: dashboard, authentication screens, voice-test interface.
- Python 3.13 + Django 5.2 + Django REST Framework: API, business data, RBAC, and call workflow.
- PostgreSQL 16 (Docker): persistent application data.
- Redis 8 (Docker): cache and future background-job broker.
- Ollama + `llama3.2:3b` (native): local conversational model; no cloud AI key is required.
- Browser `SpeechRecognition` / `webkitSpeechRecognition`: speech-to-text; use Chrome or Brave and allow microphone access.
- Browser Speech Synthesis API: text-to-speech.

## One-time setup

1. Create the application environment file:

```bash
cp .env.example .env
```

2. Start the data services:

```bash
docker compose up -d
```

PostgreSQL is exposed at `127.0.0.1:5433`, and Redis at `127.0.0.1:6380`.

3. Install and start native Ollama, then download the local model:

```bash
brew install ollama
brew services start ollama
ollama pull llama3.2:3b
```

4. Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

5. Create the database schema and demo workspace:

```bash
python3.13 manage.py migrate
python3.13 manage.py seed_demo
```

## Run the app

Open two terminals from the repository root.

Terminal 1 — Django API:

```bash
python3.13 manage.py runserver 127.0.0.1:8000
```

Terminal 2 — Next.js dashboard:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

Demo login:

```text
Email: owner@example.com
Password: demo-owner-local
```

## Test a real voice conversation

1. Sign in and open **Dashboard → Overview → Test your agent**.
2. Click **Start voice test** and allow microphone permission.
3. Wait for the greeting to finish speaking.
4. Click **Speak**, say one complete question, then pause.
5. The browser combines speech fragments into one caller turn, Django sends it to local Ollama, and the response is spoken back as one agent turn.
6. Click **End test** to save the completed call and transcript.

Use Chrome or Brave on desktop. The model service must be running; check it with:

```bash
ollama list
```

## Stop everything

Stop the two development-server terminals with `Ctrl+C`, then run:

```bash
brew services stop ollama
docker compose stop
```

These commands stop services without deleting PostgreSQL data, Redis data, or the downloaded Ollama model. Use `docker compose down` only when you want to remove the Docker containers; do not add `-v` unless you intentionally want to delete database volumes.

## Current prototype boundaries

- This is browser voice testing, not a public telephone number yet.
- Real PSTN/SIP calling will later need a telephony provider or PBX media-stream adapter.
- Appointment booking, calendar integrations, email/SMS/WhatsApp delivery, and production deployment remain future adapters.
- The agent should use only owner-approved business information from services, FAQs, and settings.
