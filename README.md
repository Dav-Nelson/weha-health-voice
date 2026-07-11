# HealthBridge Africa

> Speak in your language. Get reliable health guidance.

A multilingual voice health agent for Africa.
Currently grounded in verified health guidelines from Nigeria, Ghana, Kenya, and Ethiopia, with support for English, Nigerian Pidgin, Swahili, Twi, Oromo, and Amharic.
Built by Async Africa for The Build 2026 by NSK AI and The Udara Project.

Live: https://healthbridge-africa.vercel.app
GitHub: https://github.com/Dav-Nelson/healthbridge-africa

---

## The Problem

Health questions don't wait until you're sitting in a hospital.

Across Africa, millions of people need reliable health guidance long before they can reach a doctor. They turn to Google, but the information is often difficult to understand, written for different healthcare systems, or only available in English. Others rely on WhatsApp messages, social media, or word of mouth, where misinformation spreads quickly.

For many people in Nigeria, Ghana, Ethiopia, and Kenya, the challenge isn't just access to healthcare, it's access to trusted health information in the language they speak every day.

The result is delayed care, unnecessary anxiety, and preventable illnesses becoming emergencies.

---

## What We Built

HealthBridge Africa is a voice-first AI health agent that lets people speak
or type health questions in their own language and receive grounded,
conversational guidance drawn from a curated knowledge base built on WHO
guidelines and country-level health protocols for Nigeria, Ghana, Ethiopia,
and Kenya.

The assistant remembers context across a conversation, asks clarifying
questions instead of giving flat one-shot answers, and responds in text
with voice playback at adjustable speed.

It does not replace doctors. It helps people know when to see one.

---

## Supported Languages

English, Nigerian Pidgin, Swahili, Oromo, Twi, Amharic.

Users can switch languages at any time using the dropdown in the header.
The entire interface responds — welcome messages, placeholders, disclaimers,
FAQ, and AI responses all adapt to the selected language.

Voice transcription is strongest for English, Swahili, and Amharic, which
Whisper-large-v3 supports natively. Pidgin and Twi route through English-mode
transcription since Whisper has no dedicated model for either. Typed input
in all six languages is unaffected by this limitation.

---

## How It Works
User speaks or types

|

React Frontend (Vercel)

Language dropdown in header triggers full interface switch

OnboardingModal, ChatDisplay, BotMessageBubble,

ResponsePlayer (speed control + global audio bouncer),

SettingsPanel (multilingual, session deletion),

HelpModal (FAQ in all 6 languages),

HistoryPanel (session-scoped conversation history)

|

Node.js + Express Gateway (Railway)

helmet (security headers)

CORS locked to healthbridge-africa.vercel.app

express-rate-limit (60 req/15min general, 20 req/15min AI endpoints)

trust proxy enabled for Railway reverse proxy

Input validation (2000 char max, 10MB audio max)

Routes: /api/voice/chat, /text-chat, /speak, /history (GET + DELETE)

Session history stored and retrieved from Neon PostgreSQL

|

FastAPI AI Pipeline (Railway)

Whisper-large-v3 via Groq        voice to text
Llama-3.3-70b via Groq           language detection + English translation

with medical terminology anchors
Gemini embedding-001             query embedding (768-dim, normalized)
pgvector search (Neon)           top-5 semantically relevant chunks

from 65-chunk verified knowledge base
Llama-3.3-70b via Groq           RAG generation in user's language

with degenerate output detection,

markdown stripping, language enforcement,

character-level and sentence-level

safety checks
gTTS                             audio synthesis, in-memory, Base64

|

Text response shown immediately

Voice playback on demand at 1x, 1.5x, or 2x speed

Global audio bouncer prevents multiple responses playing simultaneously


Conversation history is stored per session in Neon PostgreSQL. The pipeline
retrieves the last 6 messages for context on every request. Users can delete
all conversation data from both device and server at any time via Settings.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React + Tailwind CSS | Vercel |
| Gateway | Node.js + Express | Railway |
| Security | helmet + express-rate-limit + trust proxy | CORS locked to Vercel domain |
| AI Pipeline | FastAPI (Python) | Railway, Dockerized |
| Database | PostgreSQL + pgvector (Neon) | Conversations + vector embeddings |
| STT | Whisper-large-v3 via Groq | Voice transcription |
| Language Detection | Llama-3.3-70b via Groq | With medical terminology anchors |
| Generation | Llama-3.3-70b via Groq | Multilingual RAG generation |
| Embeddings | Gemini embedding-001 via Google | 768-dim normalized vectors |
| TTS | gTTS | In-memory synthesis, Base64 output |
| Analytics | PostHog | Session tracking, geography, retention |
| CI | GitHub Actions | Backend and frontend test suites |

---

## Knowledge Base

15+ conditions covered per country, grounded in official national guidelines.
65 total chunks embedded via Gemini embedding-001 and stored in Neon with
pgvector for semantic retrieval.

Conditions covered: Malaria, Typhoid Fever, Cholera, Tuberculosis, HIV/AIDS,
Lassa Fever, Meningitis, Dengue Fever, Measles, Chickenpox, Mpox,
Scabies, Ringworm, Eczema, Conjunctivitis, Jaundice, Malnutrition,
Hypertension, Diabetes, Sickle Cell Disease, Schistosomiasis,
Maternal and Neonatal Health.

Sources:
- WHO Global Health Guidelines
- Nigeria: NCDC and Federal Ministry of Health
- Ghana: Ghana Health Service
- Kenya: Ministry of Health
- Ethiopia: FMoH Ethiopia and Ethiopian Public Health Institute

See ai-pipeline/knowledge-base/sources.md for full source attribution.

---

## Security

| Control | Implementation |
|---|---|
| HTTP security headers | helmet.js |
| CORS | Locked to healthbridge-africa.vercel.app only |
| Reverse proxy trust | app.set('trust proxy', 1) for Railway |
| Rate limiting | 60 req/15min general, 20 req/15min AI endpoints |
| Input validation | 2000 character max on all text inputs |
| File upload limit | 10 MB via multer |
| SQL injection | Parameterized queries throughout (psycopg2 + node-postgres) |
| Secrets management | All keys in .env files, excluded via .gitignore |
| HTTPS | Enforced at platform level by Vercel and Railway |

---

## Data and Privacy

Conversations are stored in Neon PostgreSQL, linked only to an anonymous
device session ID. No name, email, or personal identity is collected.

Users can delete all conversation data from both device and server at any
time via Settings, which calls DELETE /api/voice/history/:sessionId and
clears localStorage simultaneously.

Automatic data expiry after 90 days is planned and not yet implemented.

---

## Known Limitations

Twi, Amharic, and Oromo language quality is inconsistent. The pipeline
detects broken or degenerate output using character-level, word-level, and
sentence-level checks, and substitutes honest fallback messages in the user's
own language when generation fails. But many queries in these three languages
still return the fallback rather than a real answer. This is a base model
training data gap, not a prompt engineering problem.

Pidgin and Twi voice transcription route through English-mode Whisper,
degrading accuracy for voice input in these two languages specifically.

Disease imagery was partially implemented using Wikimedia Commons URLs but
most images returned 404 in production testing. The feature was removed
before final submission and is listed as a roadmap item.

No user authentication exists. Sessions are device-bound via localStorage.

The FAQ panel translations were added by Ibukun in Week 6 but have not been
validated by native speakers for all six languages.

---

## Getting Started

```bash
git clone https://github.com/Dav-Nelson/healthbridge-africa.git
cd healthbridge-africa

# Backend dependencies
npm install

# Frontend dependencies
cd client && npm install && cd ..

# AI pipeline dependencies
cd ai-pipeline && pip install -r requirements.txt && cd ..

# Environment variables
cp .env.example .env
# Root .env: GROQ_API_KEY, DATABASE_URL
# client/.env: REACT_APP_API_URL
# ai-pipeline/.env: GROQ_API_KEY, GEMINI_API_KEY, DATABASE_URL

# Run backend
npm run dev

# Run frontend (separate terminal)
cd client && npm start

# Run AI pipeline (separate terminal, from ai-pipeline/)
uvicorn api.main:app --reload --port 8000
```

---

## Ingesting the Knowledge Base

Run once after cloning, or whenever knowledge base documents change:

```bash
cd ai-pipeline
python -m rag.ingest_to_db
```

Clears all existing chunks, re-embeds all five documents via Gemini
embedding-001, and stores vectors in Neon. Requires DATABASE_URL and
GEMINI_API_KEY in ai-pipeline/.env.

---

## Running Tests

```bash
# Backend tests
npm test

# Frontend tests
cd client && npm test -- --watchAll=false
```

---

## Architecture Decisions and Trade-offs

**Why Groq for generation instead of Gemini 2.5 Flash:**
Gemini 2.5 Flash's thinking mode consumed the majority of the token budget
before generating any output, causing responses to be cut off mid-sentence
in Amharic and Pidgin. Llama-3.3-70b via Groq produces complete responses
reliably and is already used for language detection, keeping the external
API surface minimal.

**Why Gemini embedding-001 for retrieval:**
Switched from local sentence-transformers in Week 3 because sentence-transformers
required torch, which exceeded Render's 512MB free tier memory limit and
caused container crashes on every cold start. Gemini embedding-001 runs via
API, has no local memory footprint, and produces 768-dim embeddings with
strong semantic accuracy.

**Why Neon PostgreSQL with pgvector instead of a dedicated vector database:**
Keeps conversation history and vector embeddings in a single free-tier
database, reducing infrastructure complexity and cost. Neon's serverless
architecture handles variable load well within the free tier constraints.

**Why Railway instead of Render:**
Render suspended both services on June 24, 2026 after free tier compute
hours were exhausted by team testing. Railway provides comparable free tier
infrastructure without requiring a credit card and supports Docker deployment
for the Python pipeline.

**Why gTTS instead of Kokoro or ElevenLabs:**
gTTS is the only free TTS engine that supports Swahili and Amharic natively.
Kokoro was evaluated in Week 1 and dropped because it required GPU compute
unavailable on the free tier. ElevenLabs has no free tier for production use.

---

## Project Structure
healthbridge-africa/

client/                   React frontend (Vercel)

src/

components/           Header (language dropdown), ChatDisplay,

BotMessageBubble, ResponsePlayer,

SettingsPanel, HelpModal, HistoryPanel

OnboardingModal.js    Language selection on first visit

App.js                Main app, language state, session management

utils/tracking.js     PostHog analytics

server/                   Node.js + Express gateway (Railway)

routes/

voice.js              /chat, /text-chat, /speak, /history (GET+DELETE)

health.js             /health endpoint

db/                     Neon PostgreSQL connection

ai-pipeline/              FastAPI RAG pipeline (Railway, Dockerized)

api/main.py             /ask, /transcribe, /speak, /health endpoints

rag/

query.py              Full RAG pipeline with safety nets

ingest_to_db.py       Knowledge base chunking and embedding

tts/speak.py            gTTS synthesis with language routing

knowledge-base/         WHO + 4 country health documents (65 chunks)

Dockerfile              Dynamic PORT for Railway deployment

tests/                    Backend test suite

.github/workflows/        CI: backend and frontend on every push

---

## The Team

| Name | Country | Role |
|---|---|---|
| David Nelson | Nigeria | Team lead, backend, RAG pipeline, security, deployment |
| Ibukun Oluwafemi | Nigeria | Frontend, UI/UX, African design system, multilingual interface |
| Ibsa Magarsa | Ethiopia | AI pipeline engineering, Amharic and Oromo validation |
| Peggy Eyram Attah | Ghana | User research, tester recruitment, Twi validation |

---

## Safety Disclaimer

HealthBridge Africa is an information and triage tool only. It does not
diagnose, prescribe, or replace professional medical advice. Every response
includes guidance on when to seek professional care. Always consult a
qualified healthcare provider for medical decisions.

---

## License

MIT. See LICENSE.

Built across Nigeria, Ethiopia, and Ghana.
The Build 2026 by NSK AI and The Udara Project.