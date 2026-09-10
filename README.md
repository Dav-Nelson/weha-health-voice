# Weha Health app

Speak in your language. Get maternal-health guidance that acts.

A voice-first health agent. Weha Health combines a general RAG-based healtha companion with a maternal-health voice triage agent that extracts symptoms across a natural, multi-turn conversation, assesses urgency against WHO-aligned danger signs, and when a result is urgent, autonomously alerts a care team via WhatsApp and Telegram, looks up the nearest health facility, and generates a shareable visit record.

Live: https://weha-health-voice.vercel.app (custom domain https://wehahealth.me coming before submission)
GitHub: https://github.com/Dav-Nelson/weha-health-voice

Built on top of HealthBridge Africa, a general multilingual health assistant our team built and shipped. That project validated real demand (300+ visits across 4+ African countries, a 100+ person WhatsApp waitlist) for voice-first, local-language health tools. Weha Health is a substantial evolution of that codebase: rebuilt around a focused maternal-health agentic flow, a new language set, and a four-model speech benchmark.

## The Problem

Pregnant women and their families across Nigeria, Ghana, and Ethiopia often don't recognize the danger signs that mean a pregnancy complication needs urgent care, and they don't always have someone to ask in the moment, in the language they actually speak. General health information exists online, but it isn't grounded in local health guidance, isn't built for how people naturally code-switch between English and Pidgin, Yoruba, Akan, or Amharic mid-sentence, and doesn't do anything with what a person tells it beyond generating text.

## What We Built

Weha Health has two integrated flows:

**Voice Triage (the flagship, agentic flow).** A user describes symptoms by voice, in whatever language mix feels natural. The system asks follow-up questions across multiple turns until it has enough structured information, checks it against WHO-aligned maternal and general danger signs, and on an urgent result:
- Sends an alert with the extracted symptoms to the user's care team over WhatsApp and Telegram, independently, so one channel's outage doesn't lose the alert
- Looks up the nearest hospital or clinic using OpenStreetMap, with a map link, and falls back to a curated list of known facilities per language/region if the live lookup is unavailable
- Generates a plain-language Visit Summary the user can share or copy to show a health worker

This is the "voice achieves a downstream task" requirement in practice: voice input drives real action, not just a response.

**General Consultation.** A RAG-based health companion grounded in WHO guidelines and country-level health protocols, for everyday health questions beyond the maternal-triage flow.

Both flows support voice input and voice output, and both respond in the user's selected language: English, Nigerian Pidgin, Yoruba, Akan, or Amharic.

## Supported Languages

English, Nigerian Pidgin, Yoruba, Akan, Amharic — chosen because they map to our team's own languages across Nigeria, Ghana, and Ethiopia.

Voice transcription and synthesis quality varies by language, documented honestly in Known Limitations below.

## How It Works

```
User speaks or types
        |
React Frontend (Vercel)
  OnboardingModal (language selection)
  Header (language switch)
  VoiceIntake (maternal triage flow, GPS capture, TTS playback, Visit Summary)
  ChatDisplay / General Consultation
  SettingsPanel, HelpModal, HistoryPanel
        |
Node.js + Express Gateway (Render)
  helmet, CORS locked to weha-health-voice.vercel.app
  express-rate-limit (60 req/15min general, 20 req/15min AI endpoints)
  Routes: /api/voice/*, /api/intake/*
        |
FastAPI AI Pipeline (Render, Dockerized)
  Speech-to-text: Sahara v2.5 (primary) | Whisper-large-v3 via Groq
                  | AssemblyAI | Hugging Face MMS-1b-all
  Llama-family model via Groq (openai/gpt-oss-120b): language
    detection, translation, structured field extraction, RAG generation
  Gemini embedding-001: query embeddings (768-dim, normalized)
  pgvector search (Neon): top-5 relevant knowledge-base chunks
  WHO-aligned rule engine: urgency assessment, localized guidance
  Escalation: Twilio WhatsApp Sandbox + Telegram Bot API, independent
  Facility lookup: OpenStreetMap Overpass API + language-matched static fallback
  Text-to-speech: Intron Sahara TTS (Pidgin/Yoruba/Amharic) | Meta MMS-TTS
    (Akan, and fallback for the other three) | gTTS (last-resort fallback)
        |
Text response shown immediately; voice playback on demand;
urgent results trigger care-team alerts, facility lookup, and a
shareable Visit Summary
```

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React + Tailwind CSS | Vercel |
| Gateway | Node.js + Express | Render |
| AI Pipeline | FastAPI (Python) | Render, Dockerized |
| Database | PostgreSQL + pgvector (Neon) | Conversations, triage records, embeddings |
| STT (primary) | Intron Sahara v2.5 | Built for African code-switching |
| STT (benchmark) | Whisper-large-v3 (Groq), AssemblyAI, Hugging Face MMS-1b-all | 4-model comparison |
| Language model | openai/gpt-oss-120b via Groq | Extraction, detection, RAG generation |
| Embeddings | Gemini embedding-001 | 768-dim, normalized |
| TTS | Intron Sahara TTS (primary), Meta MMS-TTS, gTTS | Sahara covers Pidgin/Yoruba/Amharic natively; MMS-TTS covers Akan (Sahara has no Akan voice) and backs up the other three; gTTS is a last-resort English-only fallback |
| Escalation | Twilio WhatsApp Sandbox + Telegram Bot API | Sent independently, both fail silently |
| Facility lookup | OpenStreetMap Overpass + Nominatim, static fallback | No API key required; fallback matched to spoken language |
| Analytics | PostHog | Session tracking |
| CI | GitHub Actions | Backend and frontend test suites |

## Knowledge Base

15+ conditions across Nigeria, Ghana, Ethiopia, and Kenya, grounded in WHO guidelines and national health protocols, embedded via Gemini embedding-001 and retrieved with pgvector. Powers the General Consultation flow. See `ai-pipeline/knowledge-base/sources.md` for full source attribution.

## Speech Benchmark

Compared across four speech-to-text engines on code-switched audio in our five target languages:

- **Intron Sahara v2.5** — purpose-built for African code-switching, used in the live product
- **Whisper-large-v3** (via Groq)
- **AssemblyAI** — no native support for our four African languages; relies on automatic language detection, included specifically to document that gap
- **Hugging Face MMS-1b-all** — no dedicated Nigerian Pidgin adapter, a documented model limitation, not a bug

Benchmark audio combines Intron's AfriSwitch dataset (CC BY-NC-SA 4.0, real-world code-switched speech, used here for evaluation, covering Pidgin, Yoruba, and Amharic) with team-recorded, consented, simulated clips in all four target languages — Akan relies solely on team recordings, since no Intron dataset covers it. Full methodology and results in `docs/benchmark-report.md`.

## Data and Privacy

Conversations are linked only to an anonymous device session ID, no name, email, or personal identity is collected. Users can delete all conversation data from both device and server at any time via Settings.

The escalation feature is a working prototype demonstrating a real agentic pathway, not a connection to live emergency dispatch — this is stated to users and in the demo video. WhatsApp alerts use Twilio's Sandbox for this prototype; a production deployment would move to WhatsApp Business Cloud API after Meta business verification.

Full detail in `docs/ethics-inclusion-note.md`.

## Known Limitations

- **Nigerian Pidgin has no dedicated MMS-TTS voice**, so Pidgin relies entirely on Sahara TTS as primary, with English-voice gTTS as the only fallback if Sahara is unavailable.
- **Akan has no Sahara TTS voice**, so Akan relies on MMS-TTS as primary, with English-voice gTTS as fallback.
- **AssemblyAI** has no native language support for Pidgin, Yoruba, Akan, or Amharic; benchmark results for these languages reflect automatic-detection fallback, not a fair native comparison.
- **Hugging Face MMS** has no Nigerian Pidgin adapter (STT or TTS).
- **WhatsApp escalation** uses Twilio's Sandbox, which requires each recipient to send a one-time join code and expires after 3 days of inactivity — a known constraint of the free-tier prototype, not the production design.
- **Facility lookup** depends on OpenStreetMap's health-facility tagging density, which varies by region; a static, language-matched fallback list covers cases where the live lookup fails or returns nothing.
- No user authentication; sessions are device-bound via localStorage.

## Project Structure

```
weha-health-voice/
├── client/                      React frontend (Vercel)
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── Header.js
│       │   ├── OnboardingModal.js
│       │   ├── ChatDisplay.js
│       │   ├── VoiceIntake.js       Maternal triage flow, TTS, GPS
│       │   ├── VisitSummary.js      Shareable post-triage record
│       │   ├── HistoryPanel.js
│       │   ├── HelpModal.js
│       │   └── SettingsPanel.js
│       ├── utils/tracking.js        PostHog analytics
│       └── App.js
├── server/                      Node.js + Express gateway (Render)
│   ├── routes/
│   │   ├── voice.js                 /chat, /text-chat, /speak, /history
│   │   ├── intake.js                /turn — multi-turn triage
│   │   └── health.js
│   └── db/
│       ├── index.js
│       └── migrations/001_triage_records.sql
├── ai-pipeline/                 FastAPI AI pipeline (Render, Dockerized)
│   ├── api/main.py                  All endpoints
│   ├── rag/
│   │   ├── query.py                 RAG pipeline, language enforcement
│   │   └── ingest_to_db.py
│   ├── triage/
│   │   ├── extract.py               Structured field extraction (LLM)
│   │   ├── rules.py                 WHO-aligned urgency rules, localized
│   │   ├── escalate.py              WhatsApp + Telegram alerts
│   │   └── facility.py              OSM nearest-facility lookup + fallback
│   ├── tts/speak.py                 Sahara TTS / MMS-TTS / gTTS chain
│   ├── benchmark/
│   │   ├── run_benchmark.py
│   │   ├── samples.csv
│   │   └── audio/
│   └── knowledge-base/
├── docs/
│   ├── solution-description.md
│   ├── ethics-inclusion-note.md
│   └── benchmark-report.md
└── tests/
```

## Getting Started

```bash
git clone https://github.com/Dav-Nelson/weha-health-voice.git
cd weha-health-voice

# Backend dependencies
npm install

# Frontend dependencies
cd client && npm install && cd ..

# AI pipeline dependencies
cd ai-pipeline && pip install -r requirements.txt && cd ..

# Environment variables — see table below
cp .env.example .env

# Run backend
npm run dev

# Run frontend (separate terminal)
cd client && npm start

# Run AI pipeline (separate terminal, from ai-pipeline/)
uvicorn api.main:app --reload --port 8000
```

### Environment Variables

**Root `.env` (server):**
```
DATABASE_URL=
AI_PIPELINE_URL=https://weha-health-voice-ai-pipeline.onrender.com
```

**`client/.env`:**
```
REACT_APP_API_URL=https://weha-health-voice.onrender.com
REACT_APP_POSTHOG_KEY=
REACT_APP_POSTHOG_HOST=https://eu.i.posthog.com
```

**`ai-pipeline/.env`:**
```
GROQ_API_KEY=
GEMINI_API_KEY=
DATABASE_URL=
SAHARA_API_KEY=
ASSEMBLYAI_API_KEY=
HF_API_KEY=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TEAM_WHATSAPP_NUMBERS=
```

### Ingesting the Knowledge Base

```bash
cd ai-pipeline
python -m rag.ingest_to_db
```

Clears existing chunks, re-embeds all knowledge-base documents via Gemini embedding-001, stores vectors in Neon.

### Running the Benchmark

```bash
cd ai-pipeline
python -m benchmark.run_benchmark
```

Reads `benchmark/samples.csv`, tests all four speech engines against each sample, writes `benchmark/results.csv`.

### Running Tests

```bash
npm test
cd client && npm test -- --watchAll=false
```

## Architecture Decisions and Trade-offs

**Why `openai/gpt-oss-120b` via Groq instead of Llama-3.3-70b:** Llama-3.3-70b was decommissioned in August 2026. This model is already integrated with our Groq client and requires no architecture change.

**Why Gemini embedding-001 for retrieval instead of local sentence-transformers:** `sentence-transformers` requires torch, which exceeded Render's free-tier memory limit and crashed the container on cold start. Gemini's API-based embeddings have no local memory footprint.

**Why Twilio WhatsApp Sandbox instead of Meta's WhatsApp Business API directly:** Meta's Business API requires business verification and template approval that can take days. Twilio's Sandbox is free, requires no card, and is functional within minutes — sufficient for this prototype. Production deployment would move to WhatsApp Business Cloud API.

**Why Telegram alongside WhatsApp:** redundancy. Twilio's Sandbox expires after 3 days of inactivity; Telegram has no such constraint, so alerts still reach the team if the WhatsApp sandbox session has lapsed.

**Why OpenStreetMap for facility lookup instead of Google Places:** no API key or billing account required, consistent with our zero-budget constraint. Trade-off: facility data density varies by region, addressed with a language-matched static fallback list.

**Why Sahara TTS as primary voice synthesis:** as the challenge's own partner API, it provides native voices for three of our four target languages (Pidgin, Yoruba, Amharic) at no cost under the same key used for transcription. Akan has no Sahara TTS voice, so Meta's MMS-TTS covers Akan and backs up the other three; gTTS remains only as a last-resort English-voice fallback if both are unavailable.

## Ethics and Responsible AI

See `docs/ethics-inclusion-note.md` for full detail on consent, privacy, and the honest framing of the escalation prototype's real-world limitations.

## Safety Disclaimer

Weha Health is an information and triage tool only. It does not diagnose, prescribe, or replace professional medical advice. Every response includes guidance on when to seek professional care. The WhatsApp/Telegram escalation is a working prototype demonstrating an agentic pathway, not a connection to real emergency dispatch services. Always consult a qualified healthcare provider for medical decisions.

## The Team

| Name | Country | Role |
|---|---|---|
| David Nelson | Nigeria | Team lead, backend, AI pipeline, escalation, deployment |
| Ibukun Oluwafemi | Nigeria | Frontend, UI/UX, Yoruba/Pidgin validation |
| Ibsa Magarsa | Ethiopia | AI pipeline engineering, Amharic validation |
| Peggy Eyram Attah | Ghana | User research, tester recruitment, Akan validation |

## License

MIT. See LICENSE.

Built across Nigeria, Ghana, and Ethiopia. Submitted to the Sahara CodeSwitch Africa Challenge, hosted by Intron Health.