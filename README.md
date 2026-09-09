# AI Caller - Local Prototype

Multi-tenant Django backend for a controlled AI business receptionist. Version 1 deliberately answers only owner-approved information, captures callback requests, and emails an owner summary.

## Architecture

`SIP/PSTN adapter (later) -> audio/STT adapter (later) -> Django receptionist API -> Business/FAQ/tools -> notification adapter`

The Django API and data model are the product core. Voice, telephony, LLM, calendar, email, WhatsApp, and SMS are replaceable adapters around it.

## Technology choices

- Python 3.13 + Django 5.2: tenant, business data, workflows, admin, and API.
- Django REST Framework: API used first by the local simulator, later by voice/telephony adapters.
- PostgreSQL 16: primary database locally and in production.
- Redis 8: Django cache and Celery broker/result backend.
- Celery: retryable owner notifications and future call-processing jobs.
- Django console-email backend: local owner-notification proof; transactional email/SMS/WhatsApp adapter replaces it in production.
- Deterministic retrieval: approved FAQs and services only. Local LLM/Ollama is an optional later phrasing adapter, never the source of business truth.
- Asterisk + PJSIP + ARI/WebSocket media: local SIP and later public telephony adapter.
- faster-whisper + Piper: later local STT/TTS adapters.

## Run it

```bash
cp .env.example .env
docker compose up -d
python3 manage.py migrate
python3 manage.py seed_demo
python3 manage.py runserver
```

In a second terminal, run the background worker:

```bash
celery -A config worker --loglevel=info
```

The Compose services are isolated from any native PostgreSQL or Redis installation:

- PostgreSQL: `127.0.0.1:5433`
- Redis: `127.0.0.1:6380`

Start a local test call:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/calls/ -H 'Content-Type: application/json' -d '{"business_slug":"bright-repairs","caller_phone":"+919999999999"}'
```

Use the returned `call_id` to send a turn, capture the lead, then complete the call. Completion prints the owner email summary in the server terminal.

## Deliberate prototype limits

No public phone number, live voice, automatic calendar booking, owner authentication, payment handling, or production secrets are included yet. These are added behind adapters after the controlled call flow is verified.
